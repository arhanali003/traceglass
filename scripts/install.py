#!/usr/bin/env python3
"""Install the bundled skill without downloads or configuration changes."""
import argparse
from pathlib import Path
import shutil
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'skills' / 'traceglass'
LOCATIONS = {'codex': '.agents', 'claude': '.claude', 'antigravity': '.agents'}


def install(client, project, dry_run=False):
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f'Project directory does not exist: {project}')
    clients = LOCATIONS if client == 'all' else [client]
    destinations = list(dict.fromkeys(project / LOCATIONS[c] / 'skills' / 'traceglass' for c in clients))
    for destination in destinations:
        if destination.exists() or destination.is_symlink():
            raise ValueError(f'Refusing to overwrite: {destination}')
        # Prevent installing through a skills directory redirected outside the project.
        if project not in destination.resolve().parents:
            raise ValueError(f'Destination escapes project through a symlink: {destination}')
    if not (SOURCE / 'SKILL.md').is_file():
        raise ValueError(f'Bundled skill not found: {SOURCE}')
    for destination in destinations:
        print(f'{"Would install" if dry_run else "Installing"}: {destination}')
    if dry_run:
        return destinations
    created = []
    try:
        for destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.mkdir()  # Exclusive creation: never merge with an existing skill.
            created.append(destination)
            shutil.copytree(SOURCE, destination, dirs_exist_ok=True)
    except OSError:
        for destination in reversed(created):
            shutil.rmtree(destination)
        raise
    return destinations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', choices=[*LOCATIONS, 'all'], required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        install(args.client, args.project, args.dry_run)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
