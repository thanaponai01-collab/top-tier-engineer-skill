# CLAUDE.md

This repo is the `verify-loop` Claude Code plugin: the main skill at
`plugin/skills/verify-loop/SKILL.md`, plus the manual-only `feature-map` skill at
`plugin/skills/feature-map/SKILL.md` (copied from top-tier-engineer main; standalone) and the
manual-only `latent-audit` skill at `plugin/skills/latent-audit/SKILL.md` (uses both when present), and the
manual-only `wire-check` skill at `plugin/skills/wire-check/SKILL.md` (uses both when present).

- Mechanics, not advice: every rule is a script or test that can fail, never a tip for the agent.

- Helper scripts live in each skill's `scripts/` and are stdlib-only Python.
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
