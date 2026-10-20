"""Downloader contract tests using tiny loopback fixtures; no model downloads."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('media_studio_download_models', ROOT / 'scripts/download-models.py')
DOWNLOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOWNLOADER)
PAYLOAD = bytes(range(256)) * 17 + b'fixture-end'


class FixtureHandler(BaseHTTPRequestHandler):
    """Serve full/ranged/broken responses from memory on 127.0.0.1 only."""

    def log_message(self, *_args):
        pass

    def do_GET(self):
        server = self.server
        server.requests.append(self.headers.get('Range'))
        body = PAYLOAD
        offset = 0
        status = 200
        range_header = self.headers.get('Range')
        if range_header and server.mode != 'ignore-range':
            offset = int(range_header.removeprefix('bytes=').removesuffix('-'))
            body = PAYLOAD[offset:]
            status = 206
        if server.mode == 'wrong-hash':
            body = bytes([body[0] ^ 1]) + body[1:]
        elif server.mode == 'short-body':
            body = body[:-7]
        elif server.mode == 'long-body':
            body += b'overrun'
        self.send_response(status)
        if status == 206:
            start = offset + (1 if server.mode == 'wrong-range' else 0)
            self.send_header('Content-Range', f'bytes {start}-{len(PAYLOAD)-1}/{len(PAYLOAD)}')
        if server.mode == 'wrong-length':
            self.send_header('Content-Length', str(len(body) + 1))
        elif server.mode not in {'short-body', 'long-body'}:
            self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='media-studio-download-test-')
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name).resolve()
        self.server.mode = 'normal'
        self.server.requests = []
        self.item = {
            'group': 'fixture', 'repo': 'fixture/local', 'revision': 'a' * 40,
            'source_path': 'sample.bin', 'path': 'models/fixture/sample.bin',
            'url': f'http://127.0.0.1:{self.server.server_port}/sample.bin',
            'bytes': len(PAYLOAD),
            'checksum': {'algorithm': 'sha256', 'value': hashlib.sha256(PAYLOAD).hexdigest()},
        }
        self.target = DOWNLOADER.target_path(self.data, self.item['path'])
        self.catalog = {'schema_version': 1, 'groups': {'fixture': {'files': 1, 'bytes': len(PAYLOAD)}},
                        'files': [self.item], 'total_files': 1, 'total_bytes': len(PAYLOAD)}

    def seed_partial(self, size):
        self.target.parent.mkdir(parents=True)
        partial, meta = DOWNLOADER.partial_paths(self.target)
        partial.write_bytes(PAYLOAD[:size])
        meta.write_text(json.dumps(DOWNLOADER.partial_identity(self.item)), encoding='utf-8')
        return partial, meta

    def run_main(self, args):
        with mock.patch.object(DOWNLOADER, 'load_catalog', return_value=self.catalog), contextlib.redirect_stdout(io.StringIO()):
            return DOWNLOADER.main(args)

    def assert_not_published(self):
        self.assertFalse(self.target.exists())

    def test_valid_complete_file_is_skipped_without_http(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(PAYLOAD)
        self.assertEqual(self.run_main(['--group', 'fixture', '--data-dir', str(self.data), '--reserve-gib', '0', '--download']), 0)
        self.assertEqual(self.server.requests, [])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertFalse((self.data / '.media-studio-download.lock').exists())

    def test_resume_uses_range_206_and_publishes_verified_bytes(self):
        offset = 1234
        partial, meta = self.seed_partial(offset)
        DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assertEqual(self.server.requests, [f'bytes={offset}-'])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertFalse(partial.exists())
        self.assertFalse(meta.exists())

    def test_range_ignored_200_restarts_without_appending_duplicate_prefix(self):
        self.server.mode = 'ignore-range'
        self.seed_partial(1234)
        DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assertEqual(self.server.requests, ['bytes=1234-'])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_complete_verified_partial_publishes_without_http(self):
        self.seed_partial(len(PAYLOAD))
        DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assertEqual(self.server.requests, [])
        self.assertEqual(self.target.read_bytes(), PAYLOAD)

    def test_full_checksum_failure_retains_partial_without_publishing(self):
        self.server.mode = 'wrong-hash'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assert_not_published()
        partial, meta = DOWNLOADER.partial_paths(self.target)
        self.assertEqual(partial.stat().st_size, len(PAYLOAD))
        self.assertTrue(meta.is_file())

    def test_short_response_is_retained_for_resume(self):
        self.server.mode = 'short-body'
        with self.assertRaises(OSError):
            DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assert_not_published()
        partial, _ = DOWNLOADER.partial_paths(self.target)
        self.assertEqual(partial.read_bytes(), PAYLOAD[:-7])
        self.server.mode = 'normal'
        DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assertEqual(self.target.read_bytes(), PAYLOAD)
        self.assertEqual(self.server.requests[-1], f'bytes={len(PAYLOAD)-7}-')

    def test_long_response_is_rejected_without_publishing(self):
        self.server.mode = 'long-body'
        with self.assertRaisesRegex(ValueError, 'too many bytes'):
            DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assert_not_published()

    def test_wrong_content_length_is_rejected_before_body_write(self):
        self.server.mode = 'wrong-length'
        with self.assertRaisesRegex(ValueError, 'Response size'):
            DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assert_not_published()
        self.assertFalse(DOWNLOADER.partial_paths(self.target)[0].exists())

    def test_wrong_content_range_is_rejected_without_changing_existing_part(self):
        self.server.mode = 'wrong-range'
        partial, _ = self.seed_partial(1234)
        with self.assertRaisesRegex(ValueError, 'Content-Range'):
            DOWNLOADER.transfer(self.item, self.target, retries=0)
        self.assert_not_published()
        self.assertEqual(partial.read_bytes(), PAYLOAD[:1234])

    def test_conflicting_destination_is_never_overwritten(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b'existing user file')
        with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
            DOWNLOADER.inspect_files(self.data, [self.item])
        self.assertEqual(self.target.read_bytes(), b'existing user file')
        self.assertEqual(self.server.requests, [])

    def test_partial_identity_mismatch_is_rejected(self):
        partial, meta = self.seed_partial(100)
        changed = DOWNLOADER.partial_identity(self.item)
        changed['url'] += '?changed'
        meta.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            DOWNLOADER.inspect_files(self.data, [self.item])
        self.assertEqual(partial.read_bytes(), PAYLOAD[:100])

    def test_insufficient_disk_space_fails_before_network_or_writes(self):
        with mock.patch.object(DOWNLOADER.shutil, 'disk_usage', return_value=SimpleNamespace(free=1)):
            with self.assertRaisesRegex(OSError, 'Insufficient'):
                self.run_main(['--group', 'fixture', '--data-dir', str(self.data), '--reserve-gib', '0', '--download'])
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual(self.server.requests, [])

    def test_disk_preflight_counts_only_remaining_and_reserve(self):
        states = [{'remaining_bytes': 10}, {'remaining_bytes': 20}, {'remaining_bytes': 0}]
        with mock.patch.object(DOWNLOADER.shutil, 'disk_usage', return_value=SimpleNamespace(free=35)):
            result = DOWNLOADER.disk_preflight(self.data, states, 5)
        self.assertEqual(result['required_free_bytes'], 35)

    def test_target_rejects_escape_absolute_backslash_and_drive_paths(self):
        for relative in ['../escape', '/models/escape', 'models/../../escape', 'models\\escape', 'C:/models/escape', 'models/a:b']:
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                DOWNLOADER.target_path(self.data, relative)
        self.assertEqual(list(self.data.iterdir()), [])

    def test_existing_lock_is_not_replaced_or_removed(self):
        lock = self.data / '.media-studio-download.lock'
        lock.write_text('another owner', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'lock exists'):
            with DOWNLOADER.download_lock(self.data):
                self.fail('Contended lock must never be entered')
        self.assertEqual(lock.read_text(encoding='utf-8'), 'another owner')

    def test_owned_lock_is_released_on_exception(self):
        lock = self.data / '.media-studio-download.lock'
        with self.assertRaisesRegex(RuntimeError, 'fixture error'):
            with DOWNLOADER.download_lock(self.data):
                self.assertTrue(lock.is_file())
                raise RuntimeError('fixture error')
        self.assertFalse(lock.exists())

    def test_git_blob_sha1_includes_header_and_size(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(PAYLOAD)
        item = copy.deepcopy(self.item)
        item['checksum'] = {'algorithm': 'git-blob-sha1',
                            'value': hashlib.sha1(f'blob {len(PAYLOAD)}\0'.encode('ascii') + PAYLOAD).hexdigest()}
        self.assertTrue(DOWNLOADER.verify_file(self.target, item))
        item['checksum']['value'] = hashlib.sha1(PAYLOAD).hexdigest()
        self.assertFalse(DOWNLOADER.verify_file(self.target, item))

    def test_default_plan_does_not_write_or_use_network(self):
        self.assertEqual(self.run_main(['--group', 'fixture', '--data-dir', str(self.data), '--reserve-gib', '0']), 0)
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual(self.server.requests, [])

    def test_cli_requires_explicit_absolute_data_directory(self):
        for args in [['--group', 'fixture'], ['--group', 'fixture', '--data-dir', 'relative-data']]:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                self.run_main(args)
            self.assertEqual(error.exception.code, 2)
        self.assertEqual(list(self.data.iterdir()), [])

    def test_verify_only_reports_missing_files_without_writing(self):
        with self.assertRaisesRegex(ValueError, 'missing or partial'):
            self.run_main(['--group', 'fixture', '--data-dir', str(self.data), '--reserve-gib', '0', '--verify-only'])
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual(self.server.requests, [])


class CatalogTests(unittest.TestCase):
    def test_real_catalog_contains_all_94_fixed_files_and_correct_group_totals(self):
        catalog = DOWNLOADER.load_catalog()
        self.assertEqual(len(catalog['files']), 94)
        self.assertEqual(catalog['total_files'], 94)
        self.assertEqual(catalog['total_bytes'], 62_573_344_256)
        self.assertEqual(set(catalog['groups']), {'anime', 'flux', 'wan', 'tts-preset', 'tts-clone', 'voice-design', 'index-tts', 'music'})
        self.assertEqual(sum(x['bytes'] for x in catalog['files']), catalog['total_bytes'])
        for name, group in catalog['groups'].items():
            selected = [x for x in catalog['files'] if x['group'] == name]
            self.assertEqual(len(selected), group['files'], name)
            self.assertEqual(sum(x['bytes'] for x in selected), group['bytes'], name)

    def test_catalog_checksum_provenance_has_32_lfs_and_62_git_blobs(self):
        files = DOWNLOADER.load_catalog()['files']
        self.assertEqual(sum(x['checksum']['algorithm'] == 'sha256' for x in files), 32)
        self.assertEqual(sum(x['checksum']['algorithm'] == 'git-blob-sha1' for x in files), 62)

    def test_catalog_rejects_http_and_unpinned_revisions(self):
        for field, value in [('url', 'http://huggingface.co/example'), ('revision', 'main')]:
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix='media-studio-catalog-test-') as directory:
                catalog = copy.deepcopy(DOWNLOADER.load_catalog())
                catalog['files'][0][field] = value
                path = Path(directory) / 'catalog.json'
                path.write_text(json.dumps(catalog), encoding='utf-8')
                with self.assertRaises(ValueError):
                    DOWNLOADER.load_catalog(path)

    def test_cli_list_works_without_data_directory(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/download-models.py'), '--list'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['all_files'], 94)
        self.assertEqual(output['all_bytes'], 62_573_344_256)


if __name__ == '__main__':
    unittest.main()
