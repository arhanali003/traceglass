# Contributing

The most useful contribution is a small, reproducible investigation that improves the workflow.

Include the question, a redistributable fixture or artifact identity, the client and available backend, observed results, and what remains unknown. Do not submit proprietary binaries, credentials, private captures, or invented benchmark scores.

For skill changes, explain the decision the new instruction improves. Keep format-specific details in references. For all Python changes, run:

```bash
python3 -m unittest discover -s tests -v
```

Client compatibility reports should distinguish skill discovery, invocation, and actual tool execution. Label untested integrations as untested. Keep upstream attribution intact.

## Evidence-verifier changes

Use synthetic, redistributable fixtures and temporary directories. Cover success,
tampering, malformed manifests, path traversal, symlinks and CLI exit codes. Do not
read unrelated user files in tests. Exercise the actual collector-to-verifier
handoff as well as isolated failure cases. Keep JSON result changes documented;
change `schema_version` for breaking output-contract changes.

Run the full suite before proposing a PR. GitHub Actions runs it on Linux, macOS,
and Windows with Python 3.9 and 3.13; symlink/FIFO tests may skip where unsupported.
A passing suite is not evidence of live compatibility with every AI client.

Describe the concrete behavior change, validation results, and limitations in the
PR. Update CHANGELOG.md and draft versioned notes for user-facing changes. Label
unreleased notes as drafts; do not claim a release or approval before it exists.
Only contribute material you have rights to submit under the existing MIT
license; retain attribution and do not add extracted proprietary artifacts.

## Development setup and checks

Python 3.9+ is required. The helpers have no external runtime dependencies.
Create a virtual environment with `python3 -m venv .venv`, activate it using your
platform's standard command, then run:

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
python scripts/smoke_release.py
python scripts/build_release.py --output dist/traceglass-0.2.0b1.zip
```

Ruff is development-only. No type checker is configured; do not claim a type-check
pass. Build output is a skill ZIP, not a wheel. Installation is verified from the
unpacked archive by the smoke script, without relying on the checkout's imports.
Use a fresh archive name on repeat builds: existing outputs are never overwritten.

Use small functions, standard-library facilities and Ruff formatting. For behavior
changes include a regression that fails before the fix. Mock permission failures
where OS privileges would make chmod-based tests unreliable. Avoid paid services,
network requests and execution of analyzed fixtures. Submit focused PRs describing
the trigger, fix, test evidence and any behavior changes. Maintainers should review
actual diffs and reproduce relevant scenarios; CI is not an independent review.

See [beta scenarios](BETA_TESTING.md) and [community conduct](CODE_OF_CONDUCT.md).
Proposed starter contributions (not claims of activity): a real client-discovery
report, a redistributable source-map edge fixture, improved CLI troubleshooting
based on a reproduced error, or a documented Linux/Windows beta run. Discuss the
scope before beginning a new analysis engine or large feature.
