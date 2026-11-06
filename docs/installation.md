# Installation

Requires Python 3.9+ for the optional installer. The skill itself is Markdown and has no Python runtime dependency.

From the repository root:

```bash
python3 scripts/install.py --client all --project /absolute/path/to/project --dry-run
python3 scripts/install.py --client all --project /absolute/path/to/project
```

`all` writes two copies: Codex and Antigravity share `.agents/skills/traceglass`; Claude Code uses `.claude/skills/traceglass`. Existing destinations, including symlinks, cause a refusal before copying starts. No overwrite flag is provided. To update, back up or move the existing Traceglass directory, then install again. To uninstall, remove only the installed `traceglass` directory.

Manual installation: copy the entire `skills/traceglass` folder to the appropriate directory above. Keep `references/` alongside `SKILL.md`. Start a fresh session in the target project; ask the agent to use Traceglass. In Codex use `$traceglass`; in Claude Code use `/traceglass`.

Compatibility means standard skill format and documented project discovery paths. Live testing in Codex, Claude Code, and Antigravity is pending; differences in tools, permissions, and model behavior affect investigations. This package targets local coding-agent workflows, not Claude.ai upload or cloud skill distribution.

Official references, checked 2026-11-02:

- [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Antigravity skills](https://antigravity.google/docs/skills)

If the skill is missing, check the destination and project root first. If the skill loads but binary analysis is unavailable, see [backends](backends.md); discovery and engine availability are different problems.

## Source Recovery companion

Add `--skill source-recovery` to the installer command. This installs `skills/source-recovery` under the same client-specific skills root, without replacing Traceglass. Invoke `$source-recovery` in Codex, `/source-recovery` in Claude Code, or ask Antigravity to use Source Recovery. The bundled extraction helper requires Python 3.9+. Decompilation requires a separate compatible backend.

## Local beta distribution

The proposed version is `0.2.0b1`. There is no PyPI package or published beta
release yet. A maintainer can build the skill ZIP without dependencies:

```sh
python3 scripts/build_release.py --output dist/traceglass-0.2.0b1.zip
```

Extract it with your normal ZIP tool, enter the `traceglass-0.2.0b1` directory,
and use the same `scripts/install.py` commands above. `DIST-MANIFEST.json` contains
SHA-256 hashes of packaged files; it is not a signature. The builder refuses an
existing output archive and omits developer caches and local installed skills.

A clean-install check is available as `python3 scripts/smoke_release.py`. It builds
a fresh archive, verifies hashes, installs both skills into temporary directories,
runs recovery/collection/verification, and confirms tamper detection and overwrite
refusal. It does not start an AI client or validate model-generated reports.

See [the beta guide](../BETA_TESTING.md) for first-run scenarios and feedback.
