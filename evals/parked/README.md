# Parked eval cases

Cases kept as evidence for a skill that was not built. `grade.py` and `run.py` read only
`evals/cases/`, so nothing here runs or is tested. To run one again, move its folder back into
`evals/cases/` (its skill must exist under `plugin/skills/` for `tests/test_evals.py`).

| case | skill (not built) | why parked | baseline |
|---|---|---|---|
| `dependency-health-owed-upgrades` | dependency-health | plain Opus did the work 3/3 (outcome); judge 1/3 on report wording | `results/2026-11-08-dependency-health-plain` |
| `dependency-health-came-back` | dependency-health | plain Opus fixed both reverted pins 3/3; judge 0/3 on wording | `results/2026-11-08-dependency-came-back-plain` |

Brief and reasoning: `work/briefs/dependency-health.md`, section "Eval evidence".
