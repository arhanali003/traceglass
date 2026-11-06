# Changelog

## Unreleased — proposed v0.2.0b1

- Fix misleading recovery success for skipped inputs and reject special-file roots.
- Retain collector manifests on per-directory failures; skip reparse entries.
- Reject Windows-ambiguous paths in verifier manifests on every host.
- Add file-identity checks to recovery, helper version flags, deterministic ZIP
  packaging, clean-install smoke checks, and beta/security guidance.
- Intentional behavior change: recovery returns exit 2 when skips are recorded.
- Add lint/format checks and expanded regression coverage.

### Previously implemented, still unreleased

- Add a dependency-free, read-only verifier for collected bundle manifests and
  payloads, with versioned JSON results and exit codes for agent automation.
- Detect changed/missing files and propagate original collection errors.
- Validate manifest records and reject unsafe paths, symlinks/reparse points,
  special files, duplicate outputs, and manifests larger than 16 MiB.
- Add 16 tests covering collector handoff, CLI behavior, tampering and unsafe inputs.
- Fix false change detection when path and descriptor timestamps differ in
  precision, and pin Ubuntu 24.04 to retain Python 3.9 test coverage.
- Extend existing cross-platform CI with CLI smoke verification and a job timeout.
- Document installation, examples, result semantics, contribution expectations,
  and limits of integrity verification.

Existing command names and manifest keys remain unchanged. This entry is not
a published release. See [draft beta notes](docs/releases/v0.2.0b1.md).
