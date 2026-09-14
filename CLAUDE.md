# CLAUDE.md

This repo is the `top-tier-engineer` Claude Code plugin: independent skills under `skills/<name>/SKILL.md`.

- Each skill must stand alone. No shared protocol file, no references to other skills, no required setup.
- A skill's helper scripts live in its own `scripts/` folder and are stdlib-only Python.
- Before committing: `python -m unittest discover tests`.
- Version lives in `.claude-plugin/plugin.json`; bump it and add a `CHANGELOG.md` entry per release.
