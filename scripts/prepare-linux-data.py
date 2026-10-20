#!/usr/bin/env python3
"""Plan or create Linux data-directory links without moving existing data."""

import argparse
import json
import os
from pathlib import Path
import sys


DATA_NAMES = (
    "models", "cache", "temp", "input", "output", "projects", "user", "logs"
)
SYSTEM_TREES = (
    "/bin", "/boot", "/dev", "/etc", "/lib", "/lib32", "/lib64",
    "/opt", "/proc", "/root", "/run", "/sbin", "/sys", "/usr", "/var",
)


def within(path, parent):
    """Both paths must already be absolute and resolved by the caller."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_link(path):
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def is_system_path(path):
    if path == Path(path.anchor):
        return True
    if os.name == "posix":
        return any(within(path, Path(root)) for root in SYSTEM_TREES)
    system_roots = (
        os.environ.get("SystemRoot"),
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramData"),
    )
    return any(
        within(path, Path(root).resolve()) for root in system_roots if root
    )


def build_plan(repo_root, data_dir):
    """Validate every source and target before returning a write-free plan."""
    repo_root = Path(repo_root).resolve(strict=True)
    requested_data = Path(data_dir)
    if not requested_data.is_absolute():
        raise ValueError("--data-dir must be an explicit absolute path")
    if is_link(requested_data) or not requested_data.is_dir():
        raise ValueError("--data-dir must be an existing ordinary directory")
    data_root = requested_data.resolve(strict=True)
    if not repo_root.is_dir():
        raise ValueError("repository root must be an existing directory")
    if is_system_path(data_root):
        raise ValueError("data directory cannot be a filesystem root or system path")
    if within(data_root, repo_root):
        raise ValueError("data directory cannot equal or be inside the repository")
    if within(repo_root, data_root):
        raise ValueError("repository and data directory must be separate, non-nested directories")

    operations = []
    for name in DATA_NAMES:
        source = repo_root / name
        target = data_root / name
        resolved_target = target.resolve(strict=False)
        if not within(resolved_target, data_root):
            raise ValueError("data target escapes the data directory: " + name)
        if within(resolved_target, repo_root) or within(repo_root, resolved_target):
            raise ValueError("data target overlaps the repository: " + name)
        if is_link(target):
            raise ValueError("data target must not be a symbolic link or junction: " + name)
        if target.exists() and not target.is_dir():
            raise ValueError("data target is not an ordinary directory: " + name)

        already_linked = False
        if source.is_symlink():
            if source.resolve(strict=False) != resolved_target:
                raise ValueError("repository link points elsewhere: " + name)
            already_linked = True
        elif source.exists() or is_link(source):
            raise ValueError("repository path already exists; refusing to replace: " + name)

        operations.append({
            "name": name,
            "source": str(source),
            "target": str(target),
            "target_action": "use_existing_directory" if target.exists() else "create_directory",
            "link_action": "already_linked" if already_linked else "create_symlink",
        })
    return {
        "mode": "plan",
        "repo_root": str(repo_root),
        "data_dir": str(data_root),
        "operations": operations,
    }


def prepare_data(repo_root, data_dir, apply=False):
    if apply and os.name != "posix":
        raise ValueError("--apply is supported only on POSIX systems; use the default plan on Windows")
    plan = build_plan(repo_root, data_dir)
    if not apply:
        return plan

    # All eight pairs have passed preflight before the first mkdir or symlink.
    # No deletion, rename, overwrite, mount or model operation is performed.
    for operation in plan["operations"]:
        target = Path(operation["target"])
        if operation["target_action"] == "create_directory":
            target.mkdir()
        elif is_link(target) or not target.is_dir():
            raise ValueError("data target changed after preflight: " + operation["name"])
    for operation in plan["operations"]:
        if operation["link_action"] == "create_symlink":
            Path(operation["source"]).symlink_to(
                operation["target"], target_is_directory=True
            )
    plan["mode"] = "applied"
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", required=True, type=Path,
        help="existing absolute directory on your prepared data disk; no default",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="create the validated directories and links (POSIX only); otherwise print a plan",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        result = prepare_data(repo_root, args.data_dir, apply=args.apply)
    except (OSError, ValueError, RuntimeError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
