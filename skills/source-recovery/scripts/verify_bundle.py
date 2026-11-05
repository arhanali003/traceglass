#!/usr/bin/env python3
"""Recheck collected bundle bytes without executing or modifying any artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_MANIFEST_BYTES = 16 * 1024 * 1024


def relative_path(value):
    """Accept portable collector paths, never absolute or ambiguous paths."""
    if not isinstance(value, str) or not value:
        raise ValueError('Expected a nonempty relative path')
    parts = value.split('/')
    if any(part in ('', '.', '..') for part in parts) or any(
            c in value for c in '\\:\x00'):
        raise ValueError('Unsafe manifest path: ' + repr(value))
    return parts


def regular_path(root, parts):
    """Reject symlinks, Windows junctions/reparse points and special files."""
    current = root
    for index, part in enumerate(parts):
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Link or reparse point is not allowed')
        expected = stat.S_ISREG if index == len(parts) - 1 else stat.S_ISDIR
        if not expected(info.st_mode):
            raise ValueError('Expected regular file or parent directory')
    return current


def load_manifest(root):
    path = regular_path(root, ['bundle-manifest.json'])
    with path.open('rb') as stream:
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('Manifest exceeds 16 MiB limit')
    manifest = json.loads(raw)
    if not isinstance(manifest, dict) or not all(
            isinstance(manifest.get(key), list) for key in ('files', 'errors', 'symlinks')):
        raise ValueError('Expected collector manifest with files, errors and symlinks lists')
    seen = set()
    for entry in manifest['files']:
        if not isinstance(entry, dict):
            raise ValueError('Invalid file record')
        relative_path(entry.get('path'))
        relative_path(entry.get('output'))
        if entry['output'] != 'bundle-files/' + entry['path']:
            raise ValueError('Output must match bundle-files/<path>')
        if entry['output'] in seen:
            raise ValueError('Duplicate output path: ' + entry['output'])
        seen.add(entry['output'])
        if type(entry.get('bytes')) is not int or entry['bytes'] < 0:
            raise ValueError('Invalid byte count')
        if not isinstance(entry.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
            raise ValueError('Invalid SHA-256 digest')
    return manifest


def verify(bundle):
    root = Path(bundle).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Bundle output must be a directory')
    manifest = load_manifest(root)  # Validate every record before reading payloads.
    results = []
    for entry in manifest['files']:
        item = {'path': entry['path'], 'status': 'ok'}
        try:
            path = regular_path(root, entry['output'].split('/'))
            flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
            with os.fdopen(os.open(path, flags), 'rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise ValueError('Expected regular file')
                digest = hashlib.sha256()
                size = 0
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
                    size += len(chunk)
                after = os.fstat(stream.fileno())
            item.update(bytes=size, sha256=digest.hexdigest())
            signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if signature(before) != signature(after) or signature(after) != signature(path.lstat()):
                item['status'] = 'changed_during_read'
            elif size != entry['bytes'] or digest.hexdigest() != entry['sha256']:
                item['status'] = 'mismatch'
        except FileNotFoundError:
            item['status'] = 'missing'
        except (OSError, ValueError) as error:
            item.update(status='unreadable', reason=str(error))
        results.append(item)
    failed = sum(item['status'] != 'ok' for item in results)
    return {'schema_version': 1, 'status': 'failed' if failed or manifest['errors'] else 'ok',
            'checked_files': len(results), 'failed_files': failed,
            'collection_errors': len(manifest['errors']),
            'recorded_symlinks': len(manifest['symlinks']), 'files': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, help='Directory produced by collect_bundle.py')
    args = parser.parse_args(argv)
    try:
        result = verify(args.bundle)
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({'schema_version': 1, 'status': 'error', 'error': str(error)}))
        return 1
    print(json.dumps(result))
    return 0 if result['status'] == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
