# Helper command reference

All five helpers accept `--help` and `--version`. Python 3.9+ and a trusted,
quiescent filesystem are required. Paths containing spaces must be shell-quoted.
No configuration file or environment-variable overrides are supported. These are
standalone scripts, not installed console commands or a pip package.

| Script | Required inputs | Exit 0 | Exit 1 | Exit 2 |
| --- | --- | --- | --- | --- |
| `scripts/install.py` | `--client`, `--project` | installed / dry run | invalid project, conflict or I/O error | argument usage error |
| `skills/source-recovery/scripts/recover.py` | `--target`, `--output` | completed without recorded skips | invalid target or fatal I/O error | recorded skips/partial result, or argument usage error |
| `skills/source-recovery/scripts/collect_bundle.py` | `--target`, `--output` | copied without recorded errors | invalid input or fatal I/O error | recorded collection errors, or argument usage error |
| `skills/source-recovery/scripts/verify_bundle.py` | `--bundle` | listed files match | malformed/unreadable manifest | evidence failure, or argument usage error |
| `skills/source-recovery/scripts/native_report.py` | `--target`, `--output` | tools completed, input unchanged | invalid input, missing tools, fatal I/O error | partial/failed tools or changed input, or argument usage error |

**Recovery exit 2 is new in 0.2.0b1.** Previously recorded skips still returned 0.
Update automation to inspect `manifest.json` and treat exit 2 as partial, not a
missing output. Unsupported extensions are not candidates and are silently ignored;
empty input can return 0 with zero records. Neither result proves full recovery.

Recovery prints a human summary; collection prints JSON counts; verification emits
a versioned JSON result; native reporting prints JSON job statuses. Fatal errors
are stderr text except verifier errors, which are JSON on stdout. Argument errors
always use argparse's stderr usage text. See [verifier contract](bundle-verification.md).
No verbose flag is needed for current helpers: detailed evidence is in manifests
and native stderr files. Do not use stdout alone to determine success.

## Troubleshooting

- **Python not found:** install Python 3.9+ through your normal trusted installer;
  use `python` on Windows or `python3` on macOS/Linux.
- **Existing output / installation:** choose a fresh destination. Review and move
  the old directory yourself if updating; no force-overwrite mode exists.
- **Permission denied / disk full:** inspect the manifest if present. Correct access
  or choose another filesystem; do not retry as administrator. Fatal writes can
  leave incomplete output. Retain it for diagnosis and retry in a new directory.
- **Zero recovered records:** check extensions, map `sourcesContent`, `skipped`, and
  size limits. Native/archived/remote source is not recovered by this helper.
- **Recovery partial:** symlinks, external map sections, malformed input and size
  limits can all create skipped entries. Read each reason before using the result.
- **Verifier mismatch:** preserve the original evidence; investigate the changed
  file. Do not edit hashes to make the verification pass.
- **Mach-O tools missing:** native reporting needs trusted macOS `otool`/`nm` on
  PATH. Other hosts require a separately configured analysis backend.
- **Agent cannot find skill:** check the client-specific path and restart its
  session. Discovery is separate from analysis-engine availability.
