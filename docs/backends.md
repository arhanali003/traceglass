# Analysis backends

Traceglass contributes investigation instructions, not analysis engines. Readable local files can be inspected with the agent's normal file and search tools. The included fixture demonstrates this route.

For binaries, packaged apps, or runtime investigation, connect tools appropriate to the target. [REA](https://github.com/morluto/rea) is one optional integration and the inspiration for this project's evidence discipline. Follow its current documentation for installation, provider prerequisites, supported operating systems, and client configuration. No REA source, engine, or server is bundled here.

A discovered skill cannot add tools to an already-running session. A connected MCP server may still lack a provider required for a specific format. Report such gaps explicitly and retain useful partial results.

Traceglass does not claim tested coverage of every binary format. The routing guide helps choose evidence; actual support depends on the connected backend and host.
