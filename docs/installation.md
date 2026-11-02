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
