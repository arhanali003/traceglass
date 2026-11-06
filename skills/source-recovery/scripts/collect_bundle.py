#!/usr/bin/env python3
"""Preserve regular bundle files and symlink metadata; never execute the target."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


def collect(target, output):
    target = Path(target).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if not target.is_dir():
        raise ValueError("Target must be an existing application bundle or directory")
    if output == target or target in output.parents:
        raise ValueError("Output must be outside the target")
    output.mkdir(parents=True, exist_ok=False)
    payload = output / "bundle-files"
    payload.mkdir()
    result = {
        "target": str(target),
        "files": [],
        "symlinks": [],
        "errors": [],
        "limitations": [
            "Local bundle only; no cloud or separately downloaded content.",
            "Archives and native resources are preserved, not decoded.",
            "Symlinks recorded, not followed or recreated; output is not runnable.",
            "No decompilation, original-source reconstruction, or feature-equivalence claim.",
            "No atomic filesystem snapshot; source changes are checked per file.",
        ],
    }

    def fail(path, reason):
        result["errors"].append({"path": str(path), "reason": str(reason)})

    def link(path, relative):
        try:
            result["symlinks"].append({"path": relative, "target": os.readlink(path)})
        except OSError as error:
            fail(relative, error)

    for parent, dirs, names in os.walk(
        target, followlinks=False, onerror=lambda e: fail(e.filename, e)
    ):
        for name in sorted(dirs[:]):
            path = Path(parent) / name
            rel = path.relative_to(target).as_posix()
            try:
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode):
                    link(path, rel)
                    dirs.remove(name)
                elif getattr(info, "st_file_attributes", 0) & 0x400:
                    fail(rel, "Reparse directory not followed")
                    dirs.remove(name)
                else:
                    (payload / rel).mkdir(parents=True, exist_ok=True)
            except OSError as error:
                fail(rel, error)
                dirs.remove(name)
        dirs.sort()
        for name in sorted(names):
            path = Path(parent) / name
            rel = path.relative_to(target).as_posix()
            dest = payload / rel
            try:
                before = path.lstat()
                if stat.S_ISLNK(before.st_mode):
                    link(path, rel)
                    continue
                if getattr(before, "st_file_attributes", 0) & 0x400:
                    fail(rel, "Reparse file not followed")
                    continue
                if not stat.S_ISREG(before.st_mode):
                    fail(rel, "Non-regular entry skipped")
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                sha = hashlib.sha256()
                length = 0
                flags = (
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_BINARY", 0)
                    | getattr(os, "O_NONBLOCK", 0)
                )
                fd = os.open(path, flags)
                with os.fdopen(fd, "rb") as source, dest.open("xb") as sink:
                    opened = os.fstat(source.fileno())
                    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                        before.st_dev,
                        before.st_ino,
                    ):
                        raise OSError("Source identity changed before copying")
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        sink.write(chunk)
                        sha.update(chunk)
                        length += len(chunk)
                    after = os.fstat(source.fileno())
                current = path.lstat()

                def signature(s):
                    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

                # Compare path and descriptor metadata separately: Windows can
                # report different timestamp precision for stat and fstat.
                if signature(before) != signature(current) or signature(opened) != signature(after):
                    raise OSError("Source changed during copying")
                verify = hashlib.sha256()
                with dest.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        verify.update(chunk)
                if verify.digest() != sha.digest() or length != before.st_size:
                    raise OSError("Output verification failed")
                result["files"].append(
                    {
                        "path": rel,
                        "bytes": length,
                        "sha256": sha.hexdigest(),
                        "original_mode": stat.S_IMODE(before.st_mode),
                        "output": "bundle-files/" + rel,
                        "verified": True,
                    }
                )
            except OSError as error:
                fail(rel, error)
                try:
                    if dest.exists():
                        dest.unlink()
                except OSError as cleanup_error:
                    fail(rel, f"Partial output could not be removed: {cleanup_error}")
    result["summary"] = {
        "copied_files": len(result["files"]),
        "copied_bytes": sum(f["bytes"] for f in result["files"]),
        "recorded_symlinks": len(result["symlinks"]),
        "errors": len(result["errors"]),
    }
    (output / "bundle-manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output / "REPORT.md").write_text(
        "# Local bundle preservation\n\n"
        + f"Target: `{target}`\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in result["summary"].items())
        + "\n\nAll copied files were SHA-256 verified against the bytes read from their source. "
        + "Review errors and recorded links in bundle-manifest.json.\n\n"
        + "\n".join("- " + item for item in result["limitations"])
        + "\n",
        encoding="utf-8",
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="Traceglass 0.2.0b1")
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = collect(args.target, args.output)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result["summary"]))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
