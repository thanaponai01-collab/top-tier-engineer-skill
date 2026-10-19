# CLAUDE.md

This repo is the `verify-loop` Claude Code plugin: one skill at `plugin/skills/verify-loop/SKILL.md`.

- Helper scripts live in `plugin/skills/verify-loop/scripts/` and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `plugin/.claude-plugin/plugin.json` (keep `plugin/.codex-plugin/plugin.json` in
  step); bump it and add a `CHANGELOG.md` entry per release.
