# Initial beta audit

Inspected 2026-11-06, baseline `f3d9995`, local branch `codex/bundle-verification`.
This is a first-party engineering review, not an independent security audit.

## Actual functionality

Traceglass is an instruction/skill distribution with five standalone Python
entry points: installer, source recovery, bundle collector, bundle verifier and
macOS native-report helper. Runtime dependencies are Python's standard library;
native reports additionally require trusted local `otool` and `nm` executables.
There is no Python wheel, hosted service, autonomous analysis engine, configuration
loader, or automatic feature graph/comparison command. Feature tracing and release
comparison are agent-guided playbooks. Do not advertise them as deterministic
analysis implemented by the helpers.

## Baseline verification

- 38 unittest cases passed, 0 failed, 0 skipped on local macOS/Python 3.9.6.
- Installer dry-run, all-client paths, overwrite refusal and rollback have tests.
- Recovery covers byte preservation, embedded maps, basic limits and symlinks.
- Collector/verifier handoff, tampering, malicious paths and special-file
  rejection are tested. Native-tool tests use stubs, not successful real tooling.
- Existing CI declares six OS/Python jobs (3.9/3.13 on Linux/macOS/Windows).
  No new remote CI result is claimed in this audit.
- No lint/type/build configuration or reproducible distribution build exists.

## Verified defects and priorities

1. **High, misleading success:** recovery CLI exits 0 even when the only candidate
   is malformed map JSON and zero records are recovered. Reproduced with `{`.
   Preserve the manifest but return a documented partial-result status.
2. **Medium, invalid input:** selecting a FIFO as the recovery root produces an
   empty successful manifest instead of rejecting a non-file/non-directory root.
   Reproduced using a temporary FIFO; no blocking read was attempted.
3. **Medium, partial results lost:** destination-directory creation in collection
   is outside per-entry error handling. A simulated PermissionError aborts without
   writing the manifest. Keep failures visible and continue unrelated entries.
4. **Hardening gap (code inspection):** collector and recovery skip POSIX symlinks
   but do not explicitly reject Windows reparse directories/junctions. Add explicit
   checks and a Windows-specific test; local macOS cannot establish Windows behavior.
5. **API validation gap (code inspection):** unknown installer client raises KeyError
   through the Python function. CLI choices prevent it, but callers deserve ValueError.

## Security and reliability boundaries

No target code is executed by recovery/collection/verification. Native inspection
invokes argument arrays without a shell, but external parsers still process
untrusted bytes and must be trusted/patched. Target trees must be quiescent and
under the caller's control: current checks do not provide a filesystem sandbox or
eliminate concurrent parent-directory replacement races. Outputs can contain private
paths and source text; no redaction is promised. Source maps cannot choose output
paths. Hash verification is integrity checking, not authenticity.

Recovery limits individual carrier size but has no total file/byte budget. Collector
and native reports can exhaust disk; native subprocesses have timeouts. No external
runtime Python dependencies were found, but that does not certify the Python
interpreter, OS or external tools as vulnerability-free.

## Missing verification and developer experience

Missing: clean distribution/install smoke test, CLI failure paths for recovery and
collection, permission/directory failure coverage, Windows junction coverage,
real native success, resource-bounded larger fixture, clear helper exit contracts,
version flags, beta guide and feedback template. Existing instructions require a
checkout; there is no package-manager installation to test. Use a reproducible ZIP
of the existing skill layout rather than introducing an unrelated Python framework.
Live Codex/Claude/Antigravity integration and actual external adoption are unverified.

## Implementation plan

1. Add regression tests and minimal fixes for the above findings.
2. Add consistent helper version reporting and a reproducible, non-overwriting
   ZIP builder; exercise unpacked installation and saved evidence in a clean process.
3. Add lint/format checks and build/install smoke checks to the existing CI matrix.
4. Document real capabilities, safe input assumptions, commands/exit codes,
   beta scenarios, troubleshooting and useful proposed contributions.
5. Run complete QA and record exact results in a separate final report. Keep remote
   publication, settings, releases and invitations pending user approval.

## Additional finding during implementation

The verifier's lexical path validation accepted trailing dots/spaces and Windows
device names. These are ambiguous under Windows path rules. Added portable lexical
rejection and regression cases; exploitation on Windows was not reproduced locally.
This hardening intentionally rejects additional unusual POSIX filenames.
