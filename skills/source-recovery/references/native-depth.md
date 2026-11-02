# Deep native recovery

Use this workflow when readable-file extraction is exhausted and the remaining implementation is compiled. Recover the best representation available; never relabel assembly or pseudocode as original source.

## Module identity and selection

Use the preserved bundle inventory to find real executable/library formats, not just large files. Inspect architectures, dependencies and exported symbols before inferring which library owns a feature. Preserve per-module SHA-256 and the selected architecture. A small app launcher can depend on much larger implementation libraries.

For Mach-O on macOS, the bundled `scripts/native_report.py --target /absolute/binary --output /new/directory` writes load commands, dependencies and symbols through existing `otool`/`nm`. Add `--assembly` to export the tool-selected text-section disassembly. Output streams to disk; check free space first. Each command has a timeout (default 60 seconds), records its exit status and hashes, and retains partial output on timeout. Read stderr and statuses before interpreting output. This helper performs no decompilation and does not execute the app.

## Real decompilation

Discover the current REA tool schemas and inspect `binary_session` only when selecting a provider or diagnosing a blocker. Distinguish a provider advertised by the server from an installed, usable engine. Preserve an existing user session instead of silently replacing it.

1. Select a compatible installed provider and open the explicit binary. Do not automatically install engines or change client registrations.
2. Obtain analyzed procedures using the provider's inventory/search tools. Page inventories when supported; retain exact canonical addresses and module identity. A name search is not a complete function inventory.
3. Decompile explicit addresses in small batches with `batch_decompile` or the available per-procedure equivalent. Save returned pseudocode locally, with provider version, Evidence IDs, canonical addresses and per-item failures. Do not invent missing bodies.
4. Trace relevant callers, callees, references and constants to explain a selected behavior. Unknown indirect calls and library boundaries remain unknown. Recover readable packaged resources in parallel conceptually; do not assume pseudocode describes all resources.
5. Keep a checkpoint ledger of discovered / attempted / recovered / failed / deferred procedures. Resume unresolved work only when an input, tool or question changes. Report recovery relative to the analyzed procedure inventory, never relative to all original source.
6. Export evidence before closing sessions opened for this task. Keep decompiler output separate from any new implementation.

If broad recovery is requested, process each module as a separately identified unit and report unvisited modules. An exhaustive pass through the provider's discovered functions still does not prove complete program recovery.

## Difficult artifacts

- **Stripped names:** preserve addresses; infer descriptive names only in an analyst annotation field.
- **Optimized/inlined code:** keep merged or uncertain function boundaries explicit; original function structure may be unrecoverable.
- **Obfuscated control flow:** compare pseudocode with assembly and references; do not present cosmetic renaming as deobfuscation.
- **Packed or encrypted content:** report the observed format and specific decoder requirement. Do not claim bytes have been decoded without verified output. Runtime capture is a separate scoped operation, not an automatic response to static failure.
- **Managed versus native:** choose a compatible bytecode decompiler when actual metadata/bytecode exists. Do not apply native pseudocode labels to original high-level source.
- **Unavailable engine or failed handshake:** save the exact failure and continue supported static export. Do not retry an unchanged blocked call indefinitely.
- **Server-side code:** identify the missing boundary; a local application cannot supply unshipped server implementation.

A second installed editor is a separate comparison target, never a replacement for unrecovered code. Keep outputs separated by application, version and digest. Nothing in this workflow authorizes publishing extracted proprietary files or changing licensing/entitlement state.
