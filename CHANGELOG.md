# Changelog

## Unreleased — proposed v0.2.0

- Add a dependency-free, read-only verifier for collected bundle manifests and
  payloads, with versioned JSON results and exit codes for agent automation.
- Detect changed/missing files and propagate original collection errors.
- Validate manifest records and reject unsafe paths, symlinks/reparse points,
  special files, duplicate outputs, and manifests larger than 16 MiB.
- Add 15 tests covering collector handoff, CLI behavior, tampering and unsafe inputs.
- Extend existing cross-platform CI with CLI smoke verification and a job timeout.
- Document installation, examples, result semantics, contribution expectations,
  and limits of integrity verification.

Existing installer and collector interfaces remain unchanged. This entry is not
a published release. See [draft notes](docs/releases/v0.2.0.md).
