# Verify saved bundle evidence

When an agent resumes an investigation or receives a collected bundle, recheck its
saved bytes before relying on previous observations. `verify_bundle.py` reads
`bundle-manifest.json` and the files it lists. It never executes the target,
fetches data, repairs files, or writes into the bundle. The original app is not
needed.

## Install and run

Requires Python 3.9+; no third-party packages. From a cloned Traceglass checkout:

```bash
python3 scripts/install.py --client codex --project /path/to/project --skill source-recovery
```

The verifier is installed at
`/path/to/project/.agents/skills/source-recovery/scripts/verify_bundle.py`.
For Claude use `--client claude` and `.claude` instead of `.agents`;
`--client all` installs both locations. Existing installations are never overwritten:
back up or move the old skill directory before reinstalling.

You can also run directly from the checkout:

```bash
python3 skills/source-recovery/scripts/verify_bundle.py --bundle /path/to/collected-output
```

See the [runnable example](../examples/verify-bundle.md).

## Agent contract

Normal execution writes one JSON object to stdout, including:

- `schema_version`: `1` for the verifier's result format.
- `status`: `ok`, `failed`, or `error`.
- `checked_files`, `failed_files`, `collection_errors`, `recorded_symlinks`:
  counts on a completed check.
- `files`: per-file `path` and `status`; readable files include observed `bytes`
  and `sha256`. Statuses are `ok`, `mismatch`, `missing`, `unreadable`, or
  `changed_during_read`.
- `error`: explanation when the manifest or invocation cannot be processed.

| Exit | Meaning | Agent action |
| --- | --- | --- |
| 0 | Listed files match; no collection errors recorded | Review coverage before using evidence |
| 1 | Invalid/unreadable manifest or bundle | Correct input; do not treat as verified |
| 2 | File check failed or collection reported errors | Report partial/untrusted evidence; investigate failures |

Argument parsing errors use Python argparse's usual stderr output and exit 2;
`--help` is human-readable. Automation should supply the required `--bundle`
argument, check the exit code, and parse JSON only for normal invocations.

Suggested agent instruction:

> Before using this saved bundle, run verify_bundle.py. Report its exit code,
> checked-file count, collection errors, and failed paths. Do not repair the
> evidence or execute its files. Distinguish integrity from authenticity.

## Boundaries

- Supports collector `bundle-manifest.json`, not source-recovery or native-report
  manifests. Additional manifest fields are ignored for compatibility.
- Validates all file records before reading payloads. Paths must use portable
  relative components: no traversal, absolute paths, backslashes, colons, NULs,
  empty components, or duplicate output paths. Some unusual filenames that the
  collector can preserve are intentionally rejected by this portable verifier.
- Rejects symlinks/reparse points within the bundle and non-regular payloads.
  The selected bundle root itself is resolved to its actual location.
- The manifest is limited to 16 MiB; payloads are hashed in 1 MiB chunks.
- Checks only listed file contents and sizes. Extra files, empty directories,
  permissions, recorded symlink destinations, and original source files are not
  verified. An empty file list can pass; inspect `checked_files`.
- Recorded collection errors cause failure even if all listed files match.
- Hashes are not signatures. Someone changing both the payload and manifest can
  produce a passing result. Retain a separately trusted manifest when needed.
- This is not an atomic snapshot or a sandbox against concurrent filesystem
  attackers. Keep the bundle quiescent and under your control during verification;
  per-file change checks and link rejection do not eliminate parent-path races.
- No claim of original-source recovery, licensing rights, or runtime equivalence.
