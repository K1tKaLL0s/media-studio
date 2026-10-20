"""Download a large official asset in resumable ranges, then verify its SHA-256."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("url")
    p.add_argument("destination")
    p.add_argument("--root", required=True)
    p.add_argument("--size", required=True, type=int)
    p.add_argument("--sha256", required=True)
    p.add_argument("--curl", default="curl.exe")
    p.add_argument("--proxy", default="")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--chunk-mib", type=int, default=8)
    p.add_argument("--header", action="append", default=[])
    p.add_argument("--download-url", help="Mirror transport for missing ranges; canonical source and SHA remain fixed.")
    args = p.parse_args()
    root = Path(args.root).resolve(strict=True)
    target = Path(args.destination).resolve()
    if not target.is_relative_to(root):
        raise ValueError("The destination must stay inside the designated workspace.")
    if not args.url.startswith("https://") or args.size <= 0:
        raise ValueError("An HTTPS source and a positive expected size are required.")
    download_url = args.download_url or args.url
    if not download_url.startswith("https://"):
        raise ValueError("Mirror transport must also use HTTPS.")
    expected = args.sha256.lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("A published SHA-256 digest is required.")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.stat().st_size == args.size and digest(target) == expected:
            print(json.dumps({"status": "already_verified", "path": str(target)}), flush=True)
            return
        raise ValueError("The destination exists with different content; refusing to overwrite it.")
    parts = target.with_name(target.name + ".parts")
    if parts.is_symlink() or (parts.exists() and not parts.resolve().is_relative_to(root)):
        raise ValueError("The parts directory must resolve inside the workspace.")
    parts.mkdir(exist_ok=True)
    manifest = {"url": args.url, "size": args.size, "sha256": expected,
                "chunk_bytes": args.chunk_mib * 1024 * 1024}
    if args.header:
        manifest["headers"] = args.header
    manifest_file = parts / "manifest.json"
    if manifest_file.exists() and json.loads(manifest_file.read_text()) != manifest:
        raise ValueError("The previous download used different source metadata.")
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.download_url:
        audit = root / "logs/download-transports.jsonl"
        audit.parent.mkdir(parents=True, exist_ok=True)
        with audit.open("a", encoding="utf-8") as log:
            log.write(json.dumps({"canonical_url": args.url, "download_url": download_url,
                                  "sha256": expected, "bytes": args.size,
                                  "destination": str(target), "time": time.time()}) + "\n")
    chunk = manifest["chunk_bytes"]
    jobs = [(i, start, min(start + chunk, args.size) - 1)
            for i, start in enumerate(range(0, args.size, chunk))]

    def fetch(job):
        index, start, end = job
        final = parts / f"{index:06d}.part"
        if final.exists() and final.stat().st_size == end - start + 1:
            return final
        temporary = parts / f"{index:06d}.tmp"
        command = [args.curl, "--location", "--fail", "--silent", "--show-error",
                   "--connect-timeout", "20", "--max-time", "180", "--retry", "2",
                   "--range", f"{start}-{end}", "--output", str(temporary)]
        if args.proxy:
            command += ["--proxy", args.proxy]
        else:
            command += ["--noproxy", "*"]
        for header in args.header:
            if "\n" in header or "\r" in header or ":" not in header:
                raise ValueError("Invalid HTTP header.")
            command += ["--header", header]
        command.append(download_url)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        result = subprocess.run(command, capture_output=True, text=True, creationflags=flags)
        if result.returncode:
            # Use the independent standard HTTPS stack if Schannel cannot reach a
            # certificate-revocation service. Certificate validation stays enabled.
            proxy_handler = urllib.request.ProxyHandler(
                {"https": args.proxy, "http": args.proxy} if args.proxy else {})
            opener = urllib.request.build_opener(proxy_handler)
            headers = dict(h.split(":", 1) for h in args.header)
            headers = {k.strip(): v.strip() for k, v in headers.items()}
            headers["Range"] = f"bytes={start}-{end}"
            request = urllib.request.Request(download_url, headers=headers)
            try:
                with opener.open(request, timeout=90) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{args.size}":
                        raise RuntimeError("HTTPS fallback did not return the requested range.")
                    with temporary.open("wb") as output:
                        remaining = end - start + 1
                        while remaining:
                            data = response.read(min(1024 * 1024, remaining))
                            if not data:
                                raise RuntimeError("HTTPS fallback returned a truncated range.")
                            output.write(data)
                            remaining -= len(data)
            except Exception as error:
                raise RuntimeError(f"Range {index} failed: {result.stderr.strip()}; HTTPS fallback: {error}") from error
        if temporary.stat().st_size != end - start + 1:
            raise RuntimeError(f"Range {index} returned an unexpected byte count.")
        temporary.replace(final)
        return final

    started = time.monotonic()
    completed = 0
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8)))
    try:
        futures = [pool.submit(fetch, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            future.result()
            completed += 1
            if completed % 8 == 0 or completed == len(jobs):
                print(f"Ranges complete: {completed}/{len(jobs)}", flush=True)
    except BaseException:
        for future in futures:
            future.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        pool.shutdown(wait=True)
    merged = target.with_name(target.name + ".verified-download")
    h = hashlib.sha256()
    with merged.open("wb") as output:
        for index, _, _ in jobs:
            with (parts / f"{index:06d}.part").open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(block)
                    h.update(block)
    if merged.stat().st_size != args.size or h.hexdigest() != expected:
        raise ValueError("Final size or SHA-256 verification failed; no installable file was produced.")
    merged.replace(target)
    for index, _, _ in jobs:
        (parts / f"{index:06d}.part").unlink()
    manifest_file.unlink()
    if not any(parts.iterdir()):
        parts.rmdir()
    print(json.dumps({"status": "verified", "path": str(target), "sha256": expected,
                      "bytes": args.size, "seconds": round(time.monotonic() - started, 1)}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Download stopped: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
