# Verify Loop

A single-skill Claude Code plugin cut from
[top-tier-engineer](https://github.com/thanaponai01-collab/top-tier-engineer-skill). It holds only
the `verify-loop` skill: write a check that can fail, then loop until it passes, with retained proof.

## Install (Claude Code)

```
git clone -b verify-loop-only https://github.com/thanaponai01-collab/top-tier-engineer-skill verify-loop
/plugin marketplace add <path-to-clone>
/plugin install verify-loop@thanaponai01-skills
```

Run `/verify-loop:verify-loop` with what you want verified. The skill is manual-only and the plugin
installs no hooks.

## Use with Codex

`plugin/.codex-plugin/plugin.json` exposes `plugin/skills/`. Or copy `plugin/skills/verify-loop/`
intact into a project's `.agents/skills/`.

## Layout

- `plugin/skills/verify-loop/SKILL.md` — the skill; `references/` holds its modes (change, challenge,
  CI, project recipe, compliance, handoff, triage).
- `plugin/skills/verify-loop/scripts/` — stdlib-only Python helpers (`verify.py` is the entry point).
- `examples/verify-ci/` — a small project verified fresh in CI (`.github/workflows/verify.yml`).
- `tests/` — unit tests for the helpers: `python -m unittest discover tests`.

The skill mentions `correctness-gate` and `wire-check` for deeper work; those live in the full
top-tier-engineer plugin and are not included here.
