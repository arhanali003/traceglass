#!/usr/bin/env python3
"""Build a reproducible local skill ZIP. Never uploads or publishes anything."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "VERSION",
    "SECURITY.md",
    "BETA_TESTING.md",
    "CODE_OF_CONDUCT.md",
    "pyproject.toml",
    "requirements-dev.txt",
)
DIRECTORIES = ("skills", "scripts", "examples", "docs", "assets", "tests")


def build(output, root=ROOT):
    root = Path(root).resolve()
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:b\d+)?", version):
        raise ValueError("Invalid VERSION")
    sources = [root / name for name in FILES]
    for directory in DIRECTORIES:
        base = root / directory
        info = base.lstat()
        if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Expected regular distribution directory: {base}")
        sources.extend(base.rglob("*"))
    entries = {}
    for path in sorted(sources):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Link/reparse distribution entry: {relative}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Non-regular distribution entry: {relative}")
        entries[relative.as_posix()] = path.read_bytes()
    manifest = {
        "version": version,
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()},
    }
    entries["DIST-MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive file creation prevents overwriting another release or a symlink.
    with output.open("xb") as stream:
        try:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
                for name, data in sorted(entries.items()):
                    info = zipfile.ZipInfo(f"traceglass-{version}/{name}", (1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    archive.writestr(info, data)
        except Exception:
            stream.close()
            output.unlink()
            raise
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build(args.output))
    except (OSError, ValueError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
