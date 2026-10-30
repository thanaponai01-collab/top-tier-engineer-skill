# CLAUDE.md

This repo is the `verify-loop` Claude Code plugin: the main skill at
`plugin/skills/verify-loop/SKILL.md`, plus the manual-only `feature-map` skill at
`plugin/skills/feature-map/SKILL.md` (copied from top-tier-engineer main; standalone) and the
manual-only `latent-audit` skill at `plugin/skills/latent-audit/SKILL.md` (uses both when present), and the
manual-only `wire-check` skill at `plugin/skills/wire-check/SKILL.md` (uses both when present), and the
manual-only `debug-protocol` skill at `plugin/skills/debug-protocol/SKILL.md` (maps its check for verify-loop), and the manual-only `structure-gate` skill at
`plugin/skills/structure-gate/SKILL.md` (standalone), and the manual-only `threat-model` skill at
`plugin/skills/threat-model/SKILL.md` (standalone), and the manual-only `evolve-maintain` skill at
`plugin/skills/evolve-maintain/SKILL.md` (names debug-protocol and latent-audit when present), and the
manual-only `perf-optimize` skill at `plugin/skills/perf-optimize/SKILL.md` (standalone), and the
manual-only `safe-release` skill at `plugin/skills/safe-release/SKILL.md` (standalone), and the
manual-only `arch-design` skill at `plugin/skills/arch-design/SKILL.md` (standalone; main's prose
kept on purpose, the one exception to the rule below, see BUILD.md 1.37.0), and the manual-only
`blast-radius` skill at `plugin/skills/blast-radius/SKILL.md` (standalone).

- Mechanics, not advice: every rule is a script or test that can fail, never a tip for the agent.

- Helper scripts live in each skill's `scripts/` and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `plugin/.claude-plugin/plugin.json` (keep `plugin/.codex-plugin/plugin.json` in
  step); bump it and add a `CHANGELOG.md` entry per release.

<!-- start-here -->
## Start here

- intent: BRIEF.md
- work: BUILD.md
- Before building something new, copy `work/SPEC_TEMPLATE.md` to BRIEF.md (a new skill: to
  `work/briefs/<skill>.md`) and fill it: intent, context, guardrails, freedom, gates, output.
  `python tools/spec_check.py <file>` and `tests/test_spec.py` refuse a gap; terms in `work/SPEC_TERMS.md`.
- Read these for automatic progression work; its command contract is in
  `plugin/skills/verify-loop/references/helpers.md`.
- Authorized updates refresh affected intent, evidence and Next; read-only reviews report gaps.
<!-- /start-here -->
