#!/usr/bin/env python3
"""Recover loose UTF-8 source and embedded source-map content without execution."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote_to_bytes

SOURCE_EXTENSIONS = frozenset(
    "js mjs cjs jsx ts tsx qml lua py pyw rb php sh bash zsh swift c cc cpp cxx h hpp cs java kt kts rs go frag vert glsl metal wgsl html css scss".split()
)
INLINE = re.compile(r"sourceMappingURL\s*=\s*(data:application/json[^\s*]+)")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def recover(target, output, max_file_bytes=32 * 1024 * 1024):
    target, output = Path(target).expanduser().resolve(), Path(output).expanduser().resolve()
    if not target.exists():
        raise ValueError(f"Target not found: {target}")
    if not (target.is_file() or target.is_dir()):
        raise ValueError("Target must be a regular file or directory")
    if output == target or target in output.parents:
        raise ValueError("Output must be outside the target")
    if max_file_bytes <= 0:
        raise ValueError("File budget must be positive")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "target": str(target),
        "max_file_bytes": max_file_bytes,
        "files_seen": 0,
        "records": [],
        "skipped": [],
        "limits": [
            "Loose regular files only; no archive or native resource extraction.",
            "No target execution, network fetching, or decompilation.",
            "Source extensions are candidates, not proof of authorship.",
            "Map content is decoded text, not guaranteed original file bytes.",
        ],
    }

    def skip(path, reason):
        manifest["skipped"].append({"path": str(path), "reason": reason})

    def save(data, category, carrier, carrier_hash, **extra):
        index = len(manifest["records"])
        ext = Path(extra.get("source_name", str(carrier))).suffix.lower()
        if ext.lstrip(".") not in SOURCE_EXTENSIONS:
            ext = ".txt"
        relative = Path(category) / f"{index:06d}{ext}"
        dest = output / relative
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(data)
        manifest["records"].append(
            {
                "category": category,
                "output": relative.as_posix(),
                "carrier": str(carrier),
                "carrier_sha256": carrier_hash,
                "sha256": digest(data),
                "bytes": len(data),
                **extra,
            }
        )

    def read_map(obj, carrier, carrier_hash, location, depth=0):
        if depth > 16:
            skip(carrier, f"{location}: indexed map nesting limit")
            return
        if not isinstance(obj, dict) or obj.get("version") != 3:
            skip(carrier, f"{location}: unsupported map structure/version")
            return
        sections = obj.get("sections")
        if sections is not None:
            if not isinstance(sections, list):
                skip(carrier, f"{location}: invalid sections")
                return
            for i, section in enumerate(sections):
                loc = f"{location}/section/{i}"
                if isinstance(section, dict) and "map" in section:
                    read_map(section["map"], carrier, carrier_hash, loc, depth + 1)
                else:
                    skip(carrier, f"{loc}: external or missing section map not fetched")
            return
        names, contents = obj.get("sources"), obj.get("sourcesContent")
        if not isinstance(names, list) or not isinstance(contents, list):
            skip(carrier, f"{location}: missing sources or embedded sourcesContent")
            return
        if len(names) != len(contents):
            skip(carrier, f"{location}: sources/content length mismatch; processing paired entries")
        for i, name in enumerate(names):
            if i >= len(contents) or not isinstance(contents[i], str):
                skip(carrier, f"{location}/source/{i}: source text absent")
                continue
            if not isinstance(name, str):
                skip(carrier, f"{location}/source/{i}: invalid source name")
                continue
            try:
                data = contents[i].encode("utf-8")
            except UnicodeError:
                skip(carrier, f"{location}/source/{i}: invalid Unicode source text")
                continue
            if len(data) > max_file_bytes:
                skip(carrier, f"{location}/source/{i}: decoded source exceeds file budget")
                continue
            save(
                data,
                "source-map-content",
                carrier,
                carrier_hash,
                source_name=name,
                map_location=location,
                source_index=i,
            )

    def files():
        if target.is_file():
            yield target
            return

        def onerror(error):
            skip(error.filename, str(error))

        for parent, dirs, names in os.walk(target, followlinks=False, onerror=onerror):
            for name in sorted(dirs[:]):
                p = Path(parent) / name
                try:
                    info = p.lstat()
                    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                        skip(p, "symlink or reparse directory not followed")
                        dirs.remove(name)
                except OSError as error:
                    skip(p, str(error))
                    dirs.remove(name)
            dirs.sort()
            for name in sorted(names):
                yield Path(parent) / name

    for path in files():
        manifest["files_seen"] += 1
        ext = path.suffix.lower().lstrip(".")
        try:
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                skip(path, "symlink or reparse file not followed")
                continue
            if ext not in SOURCE_EXTENSIONS and ext != "map":
                continue
            if not stat.S_ISREG(info.st_mode):
                skip(path, "not a regular file")
                continue
            flags = (
                os.O_RDONLY
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
            )
            with os.fdopen(os.open(path, flags), "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                    info.st_dev,
                    info.st_ino,
                ):
                    raise OSError("Source identity changed before reading")
                data = stream.read(max_file_bytes + 1)
                after = os.fstat(stream.fileno())

            def signature(value):
                return (
                    value.st_dev,
                    value.st_ino,
                    value.st_size,
                    value.st_mtime_ns,
                    value.st_ctime_ns,
                )

            if signature(opened) != signature(after) or signature(info) != signature(path.lstat()):
                raise OSError("Source changed during reading")
            if len(data) > max_file_bytes:
                skip(path, "file exceeds size budget")
                continue
            text = data.decode("utf-8-sig")
            if "\x00" in text:
                skip(path, "NUL bytes; not treated as readable source")
                continue
        except (OSError, UnicodeError) as error:
            skip(path, str(error))
            continue
        carrier_hash = digest(data)
        if ext == "map":
            try:
                read_map(json.loads(text), path, carrier_hash, "standalone")
            except (ValueError, RecursionError) as error:
                skip(path, f"Invalid map: {error}")
            continue
        save(data, "shipped-source", path, carrier_hash)
        for i, match in enumerate(INLINE.finditer(text)):
            try:
                header, payload = match[1].split(",", 1)
                raw = unquote_to_bytes(payload)
                if ";base64" in header:
                    raw = base64.b64decode(raw, validate=True)
                if len(raw) > max_file_bytes:
                    raise ValueError("inline map exceeds file budget")
                read_map(json.loads(raw.decode("utf-8-sig")), path, carrier_hash, f"inline/{i}")
            except (ValueError, UnicodeError, RecursionError) as error:
                skip(path, f"Invalid inline map: {error}")
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    counts = {
        kind: sum(r["category"] == kind for r in manifest["records"])
        for kind in ["shipped-source", "source-map-content"]
    }
    (output / "REPORT.md").write_text(
        "# Source recovery\n\n"
        + f"Target: `{target}`\n\n"
        + f"Files encountered: {manifest['files_seen']}\n\n"
        + f"Exact shipped source copies: {counts['shipped-source']}\n\n"
        + f"Embedded source-map texts: {counts['source-map-content']}\n\n"
        + f"Skipped entries/issues: {len(manifest['skipped'])}\n\n"
        + "See manifest.json for hashes, carrier paths, map indices and skipped entries.\n\n"
        + "No compiled code was decompiled. No build or runtime equivalence was tested. "
        + "Counts do not measure recovered functionality. Bundled third-party code may be included.\n",
        encoding="utf-8",
    )
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version="Traceglass 0.2.0b1")
    p.add_argument("--target", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--max-file-mib", type=int, default=32)
    args = p.parse_args()
    try:
        result = recover(args.target, args.output, args.max_file_mib * 1024 * 1024)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Recovered {len(result['records'])} records; output: {args.output.resolve()}")
    return 2 if result["skipped"] else 0


if __name__ == "__main__":
    sys.exit(main())
