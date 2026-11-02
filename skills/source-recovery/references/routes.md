# Recovery routes

Prefer fidelity over volume. Inspect file magic or format-aware metadata before selecting a tool. The skill installs no engines or MCP servers.

| Artifact | Route | Expected output |
| --- | --- | --- |
| Readable scripts / QML / shaders | Bundled helper | Exact shipped file bytes |
| JSON source maps with sourcesContent | Bundled helper, including inline data maps and indexed inline sections | Embedded source text with carrier hash and index |
| ASAR / ZIP / JAR / APK | Connected format-aware inventory and extraction into a new directory, then run helper on extracted files | Container entries; bytecode still needs decompilation |
| .NET managed assembly | Compatible managed decompiler, such as an available ILSpy integration | Approximate C#; project reconstruction may need dependencies/resources |
| JVM / Android bytecode | Available Java/DEX decompiler, such as JADX | Approximate Java; original Kotlin/Java structure may be lost |
| Python bytecode | Decompiler explicitly supporting the bytecode's Python version | Approximate Python or an explicit unsupported-version result |
| Native Mach-O / PE / ELF | Available REA provider, Ghidra, IDA, or Hopper | Assembly and approximate pseudocode; not original C++/Swift/Rust |
| WebAssembly | Available WASM inspection/decompiler | WAT or approximate code, not original source |

## Packages and source maps

Use an extractor that rejects traversal, absolute output paths, escaping links, and resource-exhaustion archives. Preserve archive identity and member provenance. The helper never fetches map URLs or source paths: local sidecar maps are found by traversal, while remote maps and external indexed sections remain explicit gaps.

When a map contains filenames but no embedded text, inspect only files inside the selected artifact or explicitly supplied additional source roots. Do not resolve arbitrary paths into the user's home directory. Obfuscated/minified code remains shipped code; save formatting or renaming as a derived copy, not as the original bytes.

## Native analysis with REA

Discover the connected tool list. Open the selected binary with `open_binary`; use supported function inventory and focused analysis tools to obtain real pseudocode. Preserve returned evidence IDs and coverage. Export needed evidence and close sessions opened for this task. Do not claim a decompiler worked from tool availability or an inventory alone.

A stripped symbol table, missing provider, unsupported architecture, or unavailable debug information is a specific limitation. Installing this skill does not repair any of those. Reuse supported static extraction while explaining the exact blocker.

## Buildability

Readable files do not imply a rebuildable application. Build scripts, dependencies, generated code, native bindings, signing, assets, and server implementations can be absent. Distinguish: recovered text, parsed/decompiled code, successful build, and matching observed behavior. Never replace missing business logic with invented code and label it recovered.
