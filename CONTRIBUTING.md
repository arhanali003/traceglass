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
