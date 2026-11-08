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
manual-only `arch-design` skill at `plugin/skills/arch-design/SKILL.md` (standalone; main's prose,
see BUILD.md 1.37.0), and the manual-only
`blast-radius` skill at `plugin/skills/blast-radius/SKILL.md` (standalone), and the manual-only
`mistake-proof` skill at `plugin/skills/mistake-proof/SKILL.md` (points at evolve-maintain when present),
and the manual-only `formal-check` skill at `plugin/skills/formal-check/SKILL.md` (points at
debug-protocol for a bug it finds), and the manual-only `untangle` skill at
`plugin/skills/untangle/SKILL.md` (standalone), and the manual-only `cleanup` skill at
`plugin/skills/cleanup/SKILL.md` (points at untangle for restructuring), and the manual-only
`checkup` skill at `plugin/skills/checkup/SKILL.md` (runs structure-gate, latent-audit, arch-design
and feature-map's helpers when present; names the fixer skill per finding), and the manual-only
`dependency-health` skill at `plugin/skills/dependency-health/SKILL.md` (points at evolve-maintain
for a large upgrade), and the manual-only `state-machines` skill at
`plugin/skills/state-machines/SKILL.md` (standalone), and the manual-only `test-diet` skill at
`plugin/skills/test-diet/SKILL.md` (standalone).

## How a skill is written

A skill is a saved prompt: plain words the user would otherwise type again. It guides a capable
model, today's or a better one later, and trusts it to use its own knowledge and judgment.

- Say what is wanted, not how to do it: the goal, what done looks like, what to avoid, and the
  shape of the output that comes back. That output shape is the one thing to pin down.
- Leave the method free. No step-by-step procedures, no workarounds for a model's weak spots;
  those age badly as models improve.
- Keep it short and readable by a person: about one page of plain prose.
- The test is "did it do what the user meant", tried on a real task. Beating a plain model is not
  the goal.
- Add a script only when it does something reading cannot (an exact count, a record kept across
  sessions) and a test showed it mattered. Skills whose scripts already proved a win keep them
  (verify-loop, structure-gate, debug-protocol, checkup, feature-map, dependency-health); the rest
  move to prose when next touched.

## Repo mechanics

- Helper scripts live in each skill's `scripts/` and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `plugin/.claude-plugin/plugin.json` (keep `plugin/.codex-plugin/plugin.json` in
  step); bump it and add a `CHANGELOG.md` entry per release.

<!-- start-here -->
## Start here

- intent: BRIEF.md
- work: BUILD.md
- Before building a new skill, write a few lines in `work/briefs/<skill>.md`: why it exists and
  what output it should return. `work/SPEC_TEMPLATE.md` and `tools/spec_check.py` are optional.
- Read these for automatic progression work; its command contract is in
  `plugin/skills/verify-loop/references/helpers.md`.
- Authorized updates refresh affected intent, evidence and Next; read-only reviews report gaps.
<!-- /start-here -->
