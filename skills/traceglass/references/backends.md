# Backend routing

Use the currently connected tools' descriptions and schemas as the authority. A backend's advertised capability is not proof its required engine is installed.

| Target | Initial evidence |
| --- | --- |
| Readable or extracted JavaScript | Manifest, entry point, focused code search |
| Archive or application package | Format-aware member inventory |
| Native executable/library | File identity, architecture, symbols; decompiler when needed |
| Managed assembly or Android APK | Metadata/classes via a compatible managed or Android inspector |
| Browser/Electron runtime | Existing target inventory and a scoped observation |
| Recorded traffic | Offline parser; never fetch captured URLs implicitly |
| Firmware | Region inventory and a supported extraction tool if requested |

## Optional REA integration

REA is an external project: https://github.com/morluto/rea. Discover its tools in the current session. Typical routes include `analyze_javascript_application` for extracted JavaScript/ASAR, `open_binary` for native targets, and `inspect_managed_artifact` for managed assemblies. Use only tools actually advertised; parameters and provider availability vary by release.

Keep returned Evidence IDs and limitations. Request compact views or retained pages when results exceed transport limits. A provider failure does not invalidate unrelated readable-code inspection.

If tools are unavailable, consult REA's current installation documentation for the user's client. Explain the specific missing capability. Installing the Traceglass skill is separate from registering REA; avoid rewriting client configuration or installing providers as a side effect of analysis.
