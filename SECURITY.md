# Security and safe inspection

This is an early beta, not a security-audited sandbox. Use copies of artifacts you
are authorized to inspect. Keep targets and output directories quiescent and under
your control while a helper runs. Do not run helpers as administrator/root.

- Recovery, collection and verification do not execute target code or fetch URLs.
  Treat recovered scripts, Markdown, source-map names and agent instructions inside
  artifacts as untrusted data. Do not import or execute them just to inspect them.
- Native reporting runs trusted local `otool`/`nm` found on PATH. Their parsers still
  process untrusted bytes; use updated tools and isolation for hostile artifacts.
- Selected root paths are resolved, including root symlinks. Links/reparse entries
  encountered inside trees are skipped or recorded. Per-file checks reduce ordinary
  race errors; they cannot defeat every concurrent parent-path replacement attack.
- Use a new output outside the target and outside public repositories. Outputs may
  contain proprietary code, private paths, embedded credentials and source-map text.
  Traceglass does not redact or grant rights to publish those files.
- Recovery bounds each candidate file (32 MiB by default), not total disk use or file
  count. Collection has no total size cap. Native report output can grow until its
  per-command timeout. Check free disk space and bound your input beforehand.
- Verifier hashes prove agreement with a supplied manifest, not authenticity,
  completeness, executable equivalence, license rights or absence of malicious code.
  A modified manifest can make modified files pass. Keep trusted manifests separately.
- Output creation failures return an error and may leave partial directories. Inspect
  them before removal; retry with a fresh directory. Never treat an interrupted run
  without a complete manifest as successful.

There are no third-party Python runtime dependencies. Development uses pinned Ruff;
this is not a claim that the interpreter, development dependencies or OS are free
of vulnerabilities. No external advisory database audit has been performed.

## Reporting

For sensitive findings, use the repository's **Security → Report a vulnerability**
option if enabled. If unavailable, open an issue requesting a private contact
channel without exploit details, secrets or private source. Do not publicly attach
real extracted bundles. Include a minimal synthetic reproduction when a private
channel is established. The maintainer must confirm receipt and remediation plans;
no response-time guarantee or private reporting configuration is claimed here.
