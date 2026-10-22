# Verify Loop

A Claude Code plugin cut from
[top-tier-engineer](https://github.com/thanaponai01-collab/top-tier-engineer-skill). It holds two
skills:

- `verify-loop`: write a check that can fail, then loop until it passes, with retained proof.
- `check-the-check`: read-only. Would an existing test, suite or CI gate catch a bug? It runs the
  check in scratch copies, plants one-line bugs, finds tests that never load or never run, and runs
  a PR's new tests against the code before the change
  (`python plugin/skills/check-the-check/scripts/check.py <repo> --check "<cmd>" [--base REF]`).

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
its verdicts come back through verify-loop. The scaffold is `verify.py scaffold-skill`, the lint is
`verify.py skill-check`, and `examples/verify-create/` is a finished run.

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
- `plugin/skills/check-the-check/` — the read-only skill; `scripts/check.py` is its whole helper.
- `examples/verify-ci/` — a small project verified fresh in CI (`.github/workflows/verify.yml`).
- `examples/verify-create/` — a notes service with a generated, proven `.claude/skills/verify/`.
- `tests/` — unit tests for the helpers: `python -m unittest discover tests`.

Create mode borrows ideas from pstack's `create-verification-skill` (MIT); see `NOTICE`.
