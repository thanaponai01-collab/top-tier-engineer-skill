# CLAUDE.md

This repo is the `top-tier-engineer` Claude Code plugin: independent skills under `skills/<name>/SKILL.md`.

- No shared protocol file, no required setup. A skill may name another skill to hand off to.
- The shared philosophy lives once, in `PHILOSOPHY.md`. Skills hold only their own work.
- A skill's helper scripts live in its own `scripts/` folder and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `.claude-plugin/plugin.json`; bump it and add a `CHANGELOG.md` entry per release.
