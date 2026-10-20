"""Download selected pinned models into an explicitly chosen existing data directory."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CATALOG = Path(__file__).resolve().parents[1] / 'config/model-downloads.json'
CHUNK = 4 * 1024 * 1024


def target_path(data_dir, relative):
    relative = PurePosixPath(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] != 'models' or '\\' in str(relative) or ':' in str(relative):
        raise ValueError('Model destination must be a safe relative models/ path')
    target = data_dir.joinpath(*relative.parts)
    if not target.resolve().is_relative_to(data_dir) or target.is_symlink():
        raise ValueError('Model destination escapes the data directory or is a symlink')
    return target


def load_catalog(path=CATALOG):
    catalog = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if catalog.get('schema_version') != 1:
        raise ValueError('Unsupported model catalog version')
    seen = set()
    for item in catalog['files']:
        if item['path'] in seen or item['group'] not in catalog['groups']:
            raise ValueError('Duplicate target or unknown model group')
        seen.add(item['path'])
        if not isinstance(item['bytes'], int) or isinstance(item['bytes'], bool) or item['bytes'] <= 0:
            raise ValueError('Invalid model file size')
        if not re.fullmatch(r'[0-9a-f]{40}', item['revision']):
            raise ValueError('Model revision must be pinned to a full commit')
        url = urllib.parse.urlsplit(item['url'])
        expected = '/' + item['repo'] + '/resolve/' + item['revision'] + '/' + item['source_path']
        if url.scheme != 'https' or url.hostname != 'huggingface.co' or url.username or url.password or url.port or urllib.parse.unquote(url.path) != expected:
            raise ValueError('Model URL must match its official pinned repository and filename')
        checksum = item['checksum']
        length = {'sha256': 64, 'git-blob-sha1': 40}.get(checksum['algorithm'])
        if not length or not re.fullmatch('[0-9a-f]{' + str(length) + '}', checksum['value']):
            raise ValueError('Missing or invalid expected checksum')
    return catalog


def verify_file(path, item):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != item['bytes']:
        return False
    checksum = item['checksum']
    digest = hashlib.sha256() if checksum['algorithm'] == 'sha256' else hashlib.sha1()
    if checksum['algorithm'] == 'git-blob-sha1':
        digest.update(f"blob {item['bytes']}\0".encode('ascii'))
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            digest.update(block)
    return digest.hexdigest() == checksum['value']


def partial_paths(target):
    return target.with_name(target.name + '.part'), target.with_name(target.name + '.part.json')


def partial_identity(item):
    return {k: item[k] for k in ('url', 'bytes', 'checksum')}


def inspect_files(data_dir, selected):
    result = []
    for item in selected:
        target = target_path(data_dir, item['path'])
        if target.exists():
            if not verify_file(target, item):
                raise ValueError(f"Existing file failed size/checksum; refusing overwrite: {item['path']}")
            result.append({'path': item['path'], 'state': 'verified', 'remaining_bytes': 0})
            continue
        partial, meta = partial_paths(target)
        if partial.is_symlink() or meta.is_symlink():
            raise ValueError('Partial download paths must not be symlinks')
        present = partial.stat().st_size if partial.exists() else 0
        if partial.exists() and (not partial.is_file() or not meta.is_file() or json.loads(meta.read_text(encoding='utf-8')) != partial_identity(item)):
            raise ValueError(f"Partial download metadata differs: {item['path']}")
        if present > item['bytes']:
            raise ValueError(f"Oversized partial download: {item['path']}")
        result.append({'path': item['path'], 'state': 'resume' if present else 'missing', 'remaining_bytes': item['bytes'] - present})
    return result


def disk_preflight(data_dir, states, reserve_bytes):
    remaining = sum(x['remaining_bytes'] for x in states)
    free = shutil.disk_usage(data_dir).free
    result = {'remaining_bytes': remaining, 'reserve_bytes': reserve_bytes, 'free_bytes': free,
              'required_free_bytes': remaining + reserve_bytes}
    if remaining + reserve_bytes > free:
        raise OSError('Insufficient data disk space: ' + json.dumps(result))
    return result


@contextlib.contextmanager
def download_lock(data_dir):
    lock = data_dir / '.media-studio-download.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError('Download lock exists; check the owning process before manually removing a stale lock') from None
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump({'pid': os.getpid()}, stream)
        yield
    finally:
        lock.unlink()


def transfer(item, target, retries=2):
    """Stream to a persistent part; publish by hardlink so no existing file is replaced."""
    partial, meta = partial_paths(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    identity = partial_identity(item)
    if meta.exists():
        if json.loads(meta.read_text(encoding='utf-8')) != identity:
            raise ValueError('Partial download source changed')
    else:
        with meta.open('x', encoding='utf-8') as stream:
            json.dump(identity, stream, indent=2)
    for attempt in range(retries + 1):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset == item['bytes']:
            break
        request = urllib.request.Request(item['url'], headers={'User-Agent': 'MediaStudioPinnedDownloader/1', 'Accept-Encoding': 'identity'})
        if offset:
            request.add_header('Range', f'bytes={offset}-')
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status = response.status
                if status == 206:
                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                    if not match or int(match[1]) != offset or int(match[3]) != item['bytes'] or int(match[2]) != item['bytes'] - 1:
                        raise ValueError('Unexpected HTTP Content-Range; part retained')
                elif status == 200:
                    offset = 0  # Server ignored Range; truncate this part before restarting.
                else:
                    raise ValueError(f'Unexpected HTTP status {status}')
                length = response.headers.get('Content-Length')
                if length is not None and int(length) != item['bytes'] - offset:
                    raise ValueError('Response size does not match the pinned source file')
                written = offset
                with partial.open('ab' if offset else 'wb') as stream:
                    while block := response.read(CHUNK):
                        if written + len(block) > item['bytes']:
                            raise ValueError('Server sent too many bytes; part retained')
                        stream.write(block); written += len(block)
                if written != item['bytes']:
                    raise OSError('Incomplete response; part retained for resume')
            break
        except (OSError, urllib.error.URLError, http.client.HTTPException):
            if attempt == retries:
                raise
            time.sleep(attempt + 1)
    if not verify_file(partial, item):
        raise ValueError('Full downloaded file failed size/checksum; part retained, final file was not published')
    os.link(partial, target)  # Atomic and fails if another process created the destination.
    partial.unlink(); meta.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='List model groups and exact total sizes')
    parser.add_argument('--group', action='append', help='Model group; repeat for several groups, or use all')
    parser.add_argument('--data-dir', type=Path, help='Required existing absolute data disk directory; no default')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--download', action='store_true', help='Download after disk preflight; otherwise only plan')
    mode.add_argument('--verify-only', action='store_true', help='Verify existing files; fail if any are missing')
    parser.add_argument('--reserve-gib', type=float, default=5, help='Data disk space to leave free (default 5 GiB)')
    args = parser.parse_args(argv)
    catalog = load_catalog()
    if args.list:
        print(json.dumps({'groups': catalog['groups'], 'all_files': catalog['total_files'], 'all_bytes': catalog['total_bytes']}, indent=2)); return 0
    if not args.group or not args.data_dir or not args.data_dir.is_absolute():
        parser.error('--group and an explicit absolute --data-dir are required')
    data_dir = args.data_dir.resolve(strict=True)
    source_root = Path(__file__).resolve().parents[1]
    if not data_dir.is_dir() or data_dir == Path(data_dir.anchor) or data_dir.is_relative_to(source_root) or source_root.is_relative_to(data_dir):
        parser.error('--data-dir must be an existing dedicated directory, non-nested with the source tree, not a filesystem root')
    if not math.isfinite(args.reserve_gib) or args.reserve_gib < 0:
        parser.error('--reserve-gib must be finite and nonnegative')
    groups = set(args.group)
    if 'all' in groups:
        if len(groups) != 1: parser.error('Use all alone')
        groups = set(catalog['groups'])
    if groups - set(catalog['groups']): parser.error('Unknown group; use --list')
    selected = [f for f in catalog['files'] if f['group'] in groups]
    # Validate paths before any file-system mutation.
    states = inspect_files(data_dir, selected)
    space = disk_preflight(data_dir, states, math.ceil(args.reserve_gib * 1024**3)) if not args.verify_only else {'free_bytes': shutil.disk_usage(data_dir).free}
    print(json.dumps({'mode': 'download' if args.download else 'verify-only' if args.verify_only else 'plan',
                      'data_dir': str(data_dir), 'groups': sorted(groups), 'selected_files': len(selected),
                      'selected_bytes': sum(f['bytes'] for f in selected), 'space': space, 'files': states}, indent=2), flush=True)
    if args.verify_only:
        if any(x['state'] != 'verified' for x in states):
            raise ValueError('Some selected files are missing or partial')
        return 0
    if not args.download: return 0
    with download_lock(data_dir):
        states = inspect_files(data_dir, selected)  # Close the race before acquiring the lock.
        disk_preflight(data_dir, states, math.ceil(args.reserve_gib * 1024**3))
        for item, status in zip(selected, states):
            if status['state'] == 'verified':
                print('SKIP verified ' + item['path'], flush=True); continue
            disk_preflight(data_dir, [status], math.ceil(args.reserve_gib * 1024**3))
            transfer(item, target_path(data_dir, item['path']))
            print('VERIFIED ' + item['path'], flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
