#!/usr/bin/env python3
"""Export static Mach-O metadata, symbols and optional assembly on macOS."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

MAGIC = {bytes.fromhex(x) for x in ['feedface','cefaedfe','feedfacf','cffaedfe','cafebabe','bebafeca','cafebabf','bfbafeca']}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def export(target, output, assembly=False, timeout=60):
    target, output = Path(target).expanduser().resolve(), Path(output).expanduser().resolve()
    if timeout <= 0:
        raise ValueError('Timeout must be positive')
    if not target.is_file():
        raise ValueError('Select one native binary, not an application directory')
    with target.open('rb') as source:
        if source.read(4) not in MAGIC:
            raise ValueError('Unsupported file header: this helper accepts Mach-O candidates only')
    otool, nm = shutil.which('otool'), shutil.which('nm')
    if not otool or not nm:
        raise ValueError('macOS otool and nm are required; use a connected native provider on other hosts')
    original = sha256(target)
    output.mkdir(parents=True, exist_ok=False)
    jobs = [('headers', [otool, '-hv', str(target)]),
            ('load-commands', [otool, '-l', str(target)]),
            ('dependencies', [otool, '-L', str(target)]),
            ('symbols', [nm, '-nm', str(target)])]
    if assembly:
        jobs.append(('assembly', [otool, '-tvV', str(target)]))
    result = {'target': str(target), 'input_sha256': original, 'jobs': [],
              'tool_sha256': {path: sha256(Path(path)) for path in [otool, nm]},
              'limitations': ['Tool-decoded metadata/assembly, not recovered original source.',
                             'No decompilation or runtime execution performed.',
                             'Stripped symbols and undiscovered code remain unknown.',
                             'Assembly uses the tool-selected architecture and text section; not every executable section or slice.',
                             'Timed-out and failed outputs are partial; output disk size is not capped.']}
    for name, command in jobs:
        out, err = output / f'{name}.txt', output / f'{name}.stderr.txt'
        status, code = 'completed', None
        with out.open('wb') as stdout, err.open('wb') as stderr:
            try:
                run = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
                code = run.returncode
                if code != 0:
                    status = 'failed'
            except subprocess.TimeoutExpired:
                status = 'timeout'
            except OSError as error:
                status = 'failed'
                stderr.write(str(error).encode())
        result['jobs'].append({'name': name, 'command': command, 'status': status,
                               'exit_code': code, 'output': out.name, 'stderr': err.name,
                               'output_sha256': sha256(out), 'bytes': out.stat().st_size})
    result['input_unchanged'] = sha256(target) == original
    (output / 'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--assembly', action='store_true')
    p.add_argument('--timeout', type=int, default=60)
    args = p.parse_args()
    try:
        result = export(args.target, args.output, args.assembly, args.timeout)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    print(json.dumps({'output': str(Path(args.output).resolve()), 'input_unchanged': result['input_unchanged'],
                      'jobs': {j['name']: j['status'] for j in result['jobs']}}))
    return 0 if result['input_unchanged'] and all(j['status'] == 'completed' for j in result['jobs']) else 2


if __name__ == '__main__':
    sys.exit(main())
