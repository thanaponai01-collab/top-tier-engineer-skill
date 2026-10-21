# CLAUDE.md

This repo is the `verify-loop` Claude Code plugin: one skill at `plugin/skills/verify-loop/SKILL.md`.

- Mechanics, not advice: every rule is a script or test that can fail, never a tip for the agent.

- Helper scripts live in `plugin/skills/verify-loop/scripts/` and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `plugin/.claude-plugin/plugin.json` (keep `plugin/.codex-plugin/plugin.json` in
  step); bump it and add a `CHANGELOG.md` entry per release.

<!-- start-here -->
## Start here

- intent: BRIEF.md
- work: BUILD.md
- Read these for automatic progression work; its command contract is in
  `plugin/skills/verify-loop/references/helpers.md`.
- Authorized updates refresh affected intent, evidence and Next; read-only reviews report gaps.
<!-- /start-here -->
