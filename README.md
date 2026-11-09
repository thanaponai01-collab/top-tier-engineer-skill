# Verify Loop

A Claude Code plugin cut from
[top-tier-engineer](https://github.com/thanaponai01-collab/top-tier-engineer-skill). Its main skill
is `verify-loop`: write a check that can fail, then loop until it passes, with retained proof. It
also ships `feature-map` (manual-only, `/verify-loop:feature-map`): a `FEATURES.md` of every
feature, its entry points and call traces, checked against the code by `features.py check` and
linked to VERIFY.md sections. And `latent-audit` (manual-only, `/verify-loop:latent-audit`): dead code
and layer breaches, in plain words: only code that is truly never loaded or called is deleted, every
command is rerun after, and every file that looked dead gets a verdict.
And `wire-check` (manual-only, `/verify-loop:wire-check`): is the code connected to the running
system? In plain words: every way in is run, each piece nothing reached gets a verdict naming its
first broken link, and a component you connect keeps a check that fails when the wiring breaks.
And `debug-protocol` (manual-only, `/verify-loop:debug-protocol`): the root cause, proven both ways.
`debug.py` keeps the code as it was reproduced, reruns the trigger with only the suspected lines
replaced, and accepts a fix only at the cause, held by a check that fails with the cause put back.
And `structure-gate` (manual-only, `/verify-loop:structure-gate`): is it spaghetti, measured?
`structure.py --gate` reports the share of code a parser actually entered before any finding, makes
every region no parser entered get a counted reading or UNKNOWN, and refuses a clean verdict over
code no linter or test can reach.
And `threat-model` (manual-only, `/verify-loop:threat-model`): what can an attacker make it do?
Every way in is attacked or shown to have nothing behind it, worst first, each attack run and
kept as a test the suite runs, and a fix shown passing now and failing with the change taken out.
And `evolve-maintain` (manual-only, `/verify-loop:evolve-maintain`): change a running system without
breaking it. A plain-prose skill: keep what each command users and jobs run prints and writes
before the edit, exercise every reader of a changed name (or say why the change cannot reach it),
and rerun every command after: any difference not asked for is a break, fixed before the answer.
And `perf-optimize` (manual-only, `/verify-loop:perf-optimize`): make it measurably faster. A
plain-prose skill: time the work on the code as it was at two sizes, find where the time goes from
runs, keep a change only when the output is the same, it beats the noise and it aims at what the
measurement showed, and leave a check in the suite that fails when the gain is taken out.
And `safe-release` (manual-only, `/verify-loop:safe-release`): deploy, or change stored data, with
a way back that was run, not guessed. A plain-prose skill: rehearse the change, a rerun of it and
its way back on a copy of the live data, run today's code on the migrated copy (the deploy window, a
code-only revert), compare the data after the way back row for row, name every loss with the step
that causes it, and never write the live data.
And `arch-design` (manual-only, `/verify-loop:arch-design`): could the architecture be better? It
shows where the structure costs you, counted, as before/after pictures with the call chain behind
each problem, writes the top move out with its steps, proof and door, names the store or seam it is
not adding, and stops to ask which move to explore. It is main's prose skill, not a gated one.

## Install (Claude Code)

```
git clone -b verify-loop-only https://github.com/thanaponai01-collab/top-tier-engineer-skill verify-loop
/plugin marketplace add <path-to-clone>
/plugin install verify-loop@thanaponai01-skills
```

Ask to verify a change, prove a task is done, or check a claim. You can run
`/verify-loop:verify-loop` yourself, and other skills, agents and AIs can call it too: the model
picks it up when verification is asked for. Every caller gets the same answer: the verdict
(green/red/partial/stale/unverified), the `VERIFY:` line, the observed rejection, what passed and
the gaps (`verify.py report`, or `status --json` as JSON). See
`plugin/skills/verify-loop/references/answer.md`. The plugin installs no hooks.

**Create mode** generates a project-local `.claude/skills/verify/` skill named `verify`, with a
feature map, wired to the project's VERIFY.md. Any skill can then call `/verify` for that repo, and
its verdicts come back through verify-loop. The scaffold is `verify.py scaffold-skill` (`--adopt`
completes a recipe Claude Code's built-in `/verify` recorded), the lint is `verify.py skill-check`,
and `examples/verify-create/` is a finished run. Claude Code runs that skill before each commit,
so it carries a cheap `## Before a commit` path: `verify.py run . --affected`.

**Maintain mode** keeps that skill honest as the app changes. `verify.py maintain` audits it
against VERIFY.md, the saved rejection proof and the git churn since the last pass. A pass then
drives every feature live and fixes map drift without touching product code or frozen checks.

## Use with Codex

`plugin/.codex-plugin/plugin.json` exposes `plugin/skills/`. Or copy `plugin/skills/verify-loop/`
intact into a project's `.agents/skills/`.

## Automatic progression

Run `python <skill-base>/scripts/verify.py advance <repo> --json` to perform eligible mechanical
steps, bounded by `--max-steps` (default 3). It runs checks, freezes a proof-ready baseline and
finishes with strict verification. Missing proof, repairs and independent judgment return as
structured tasks for the caller. Unchanged work is not rerun; `--refresh` rechecks external changes.
See [the command contract](plugin/skills/verify-loop/references/helpers.md#advance-automatic-mechanical-progression).

## Layout

- `plugin/skills/verify-loop/SKILL.md` — the skill; `references/` holds its modes (change, challenge,
  CI, project recipe, create, maintain, compliance, answer, triage).
- `plugin/skills/verify-loop/scripts/` — stdlib-only Python helpers (`verify.py` is the entry point).
- `plugin/skills/latent-audit/` — the latent-audit skill (prose); `scripts/graph-audit.py` (import
  graph, `--layers`, `--snapshot`, `--try-delete ... --run CMD`) is optional for it and is run by
  checkup and arch-design.
- `plugin/skills/wire-check/` — the wire-check skill (prose only, no scripts).
- `plugin/skills/debug-protocol/` — the debug-protocol skill; `scripts/debug.py` (`--repro`,
  `--prove FILE:LINE --as`, `--gate --regress CMD`).
- `plugin/skills/structure-gate/` — the structure-gate skill; `scripts/structure.py` (`--gate PATHS`,
  notes in `.structure/notes.md`) over `scripts/structure-report.py` (`--json`, `--baseline FILE`).
- `plugin/skills/threat-model/` — the threat-model skill (prose only, no scripts).
- `plugin/skills/evolve-maintain/` — the evolve-maintain skill (prose only, no scripts).
- `plugin/skills/perf-optimize/` — the perf-optimize skill (prose only, no scripts).
- `plugin/skills/safe-release/` — the safe-release skill (prose only, no scripts).
- `plugin/skills/arch-design/` — the arch-design skill; `scripts/dep-map.py` and `scripts/change-map.py`
  (import graph and change history for repos too big to read), `scripts/arch-design.py check` (the
  optional `docs/arch-design.md` handoff file).
- `plugin/skills/feature-map/` — the feature-map skill; `scripts/features.py` (`init`, `check`,
  `impact`) drafts and checks `FEATURES.md`.
- `examples/verify-ci/` — a small project verified fresh in CI (`.github/workflows/verify.yml`).
- `examples/verify-create/` — a notes service with a generated, proven `.claude/skills/verify/`.
- `tests/` — unit tests for the helpers: `python -m unittest discover tests`.

Create mode borrows ideas from pstack's `create-verification-skill` (MIT); see `NOTICE`.
