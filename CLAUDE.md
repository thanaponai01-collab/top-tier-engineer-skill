# CLAUDE.md

This repo is the `top-tier-engineer` Claude Code plugin: independent skills under `skills/<name>/SKILL.md`.

- No shared protocol file, no required setup. A skill may name another skill to hand off to.
- The shared philosophy lives once, in `PHILOSOPHY.md`. Skills hold only their own work.
- A skill's helper scripts live in its own `scripts/` folder and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- A skill earns its place by making an agent better, so a new skill lands with an eval case under
  `evals/cases/` (see `evals/README.md`). Write the case first and watch an agent without the skill
  fail it; then show the skill fixing that. `evals/uncovered.txt` lists older skills with no case yet
  and may only shrink.
- After changing a skill, re-run it for real: `python evals/run.py --cases <its case>`. The unit
  tests prove the grader works; only `run.py` shows whether the skill does. Commit the refreshed
  `evals/RESULTS.md`.
- Version lives in `.claude-plugin/plugin.json`; bump it and add a `CHANGELOG.md` entry per release.
