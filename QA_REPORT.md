# Early beta QA report

Date: 2026-11-06 (Asia/Kolkata). Local host: macOS, Python 3.9.6.
Baseline: `f3d9995` on `codex/bundle-verification`; see [initial audit](AUDIT.md).
At completion of this audit, changes were local and uncommitted for review.
The owner subsequently approved committing and pushing this work to the existing
PR branch. No GitHub release/package publication, remote setting changes or tester
invitations were authorized by that push approval.

## A. Completed improvements

- Recovery formerly returned success even when malformed maps were skipped. It now
  preserves the manifest and returns 2 for recorded skips. This is a documented
  CLI behavior change. Zero candidate files without skips still returns 0 explicitly.
- Recovery rejects FIFO/special-file roots before creating output, validates opened
  file identity and change metadata, and skips symlink/reparse entries. Source files
  are never executed. Unsupported-extension symlinks remain recorded as skipped.
- Collection formerly aborted on destination-directory creation errors before
  writing its manifest. It now records the failure, prunes that subtree and continues
  unrelated files. Failed partial-file cleanup is recorded rather than masking the
  original error. Fatal inability to write the manifest remains a fatal failure.
- Collector/recovery explicitly handle reparse entries. Verifier rejects trailing
  dots/spaces, control characters and Windows device names in manifest paths. These
  lexical checks are tested locally; actual Windows filesystem behavior awaits CI.
- File opens use nonblocking/no-follow flags where available to reduce special-file
  race risks. This does not remove documented parent-directory race limitations.
- Installer validates unknown client names with ValueError. All five original
  helper CLIs now expose `--version`; a regression checks consistency with VERSION.
- Added a deterministic, exclusive-create ZIP builder, hash inventory and clean
  unpacked-install smoke check. Kept the existing standalone skill architecture;
  no wheel, new CLI framework, model dependency or remote backend was introduced.
- Added beta scenarios, feedback template, CLI/exit-code reference, troubleshooting,
  security guidance, conduct policy, proposed starter contributions and feature
  request template. Existing MIT license and upstream attribution are unchanged.
- Added pinned development Ruff checks and a six-job CI build/install workflow.
  Existing Python files were mechanically formatted; source algorithms were not
  rewritten wholesale. Runtime helpers still require only the standard library.

## B. Verification results

| Command/check actually executed | Result |
| --- | --- |
| Baseline `python3 -m unittest discover -s tests -v` | 38 passed; 0 failed; 0 skipped |
| Final `python3 -m unittest discover -s tests -q` | 56 discovered; 55 passed; 0 failed; 1 skipped |
| `/tmp/traceglass-beta-dev/bin/python -m ruff check .` | Passed |
| `/tmp/traceglass-beta-dev/bin/python -m ruff format --check .` | All 13 Python files formatted |
| `/tmp/traceglass-beta-clean/bin/python scripts/smoke_release.py` | Archive hash inventory, all-client skill installs, recovery, collection, verification, tampering and overwrite refusal passed |
| `/tmp/traceglass-beta-clean/bin/python scripts/build_release.py --output dist/traceglass-0.2.0b1.zip` | Initial archive built; final refreshed artifact is `dist/beta/traceglass-0.2.0b1.zip` |
| Extracted archive beta instructions | All 16 shell commands in BETA_TESTING.md executed with expected exit codes, including intentional failures |
| Larger synthetic collection | 300 files preserved and verified |
| Actual native-tool smoke | Authored `int main(void) { return 0; }`, compiled with clang; `native.export(..., assembly=True)` completed headers, load commands, dependencies, symbols, assembly; input unchanged; target never executed |
| `git diff --check` | Passed |
| Credential-pattern scan | No matches among 55 source/document/asset files at final scan; no secret values printed |

Final archive SHA-256: `662fef6aa9dcc42345eedccb1e867ef4dd16a46ae5e1618533742457da0c5191`.
Its ZIP CRC, hash inventory and all 16 beta commands were verified after the final build.

The skipped test is `test_real_windows_junction`, which requires Windows. Permission
failures are mocked deliberately for determinism; symlink and FIFO tests ran on this
Mac. The native unit test also uses a tool stub; that is separate from the real local
native smoke above. No coverage percentage was measured. No type checker is
configured. No external dependency-advisory or independent security audit was run.

The development venv installed only pinned Ruff beyond its standard bootstrap tools.
A separate fresh venv ran the distribution smoke without installing project/runtime
dependencies. Package metadata is VERSION + ZIP hash manifest; `pyproject.toml`
configures development checks and does not advertise pip installation.

## C. Remaining issues

Release gates before claiming general platform support:

- Run the changed CI matrix after an explicitly approved push. Local execution does
  not establish Windows/Linux or Python 3.13 results for this change.
- Test real skill discovery/invocation in available Codex, Claude Code and Antigravity
  sessions, recording exact client versions and tool availability.
- Review/merge the existing bundle-verifier PR #1 and review this local beta work.
  The inspected remote PR was still OPEN. No independent review is claimed.

Known limits accepted for a scoped beta: no total resource cap, no atomic snapshot,
no authenticity checks, no automatic code graph or behavior comparison engine,
no extraction from archives/native binaries without separate tools, and no redaction
of recovered secrets/private paths. Use trusted, quiescent input copies and synthetic
fixtures. No critical failure was found in the tested workflows; that is not proof
that none exist outside their scope.

Optional follow-ups: total file/byte budgets, additional map formats, measured
performance on larger fixtures, and deeper platform-specific fault testing. Pursue
these based on genuine tester feedback rather than adding activity for appearance.

## D. Developer beta readiness

**READY WITH LIMITATIONS** for 5–10 developers using the documented helper workflows
and recording client/platform compatibility as exploratory testing. It is not yet
appropriate to call this production-ready across all clients or a security sandbox.
The working software, repeatable examples and feedback instructions are ready;
external tester participation and adoption remain unestablished.

## E. Suggested release version

`0.2.0b1`, a beta of the still-unreleased 0.2.0 work. Recovery exit-code changes and
stricter portable paths must be highlighted. Draft notes are in
[docs/releases/v0.2.0b1.md](docs/releases/v0.2.0b1.md). No tag/release was created.

## F. Next maintainer actions

1. Review the local diff and approve a push/PR plan. The mission explicitly says:
   “Do not publish packages, create GitHub releases, push branches, or modify remote
   repository settings without my explicit approval.”
2. Verify all remote CI jobs, arrange substantive review and resolve findings before
   merging the existing verifier PR plus the beta changes.
3. Approve a versioned prerelease and its reviewed archive, if desired. Confirm a
   private security contact/reporting channel; this work did not enable one.
4. Personally invite a small relevant tester group with BETA_TESTING.md; request
   sanitized feedback and permission before quoting any response publicly.
5. Reproduce reports, explain decisions in reviews, release fixes and retain genuine
   evidence. Do not equate these engineering artifacts with adoption or eligibility.
