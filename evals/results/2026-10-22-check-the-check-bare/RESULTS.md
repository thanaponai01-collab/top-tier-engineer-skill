# Scorecard — does verify-loop make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-22-0729
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.18.2
- **Cost of this run:** $1.04
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.304 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-22-check-the-check-bare/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `check-the-check-green-gate-lets-bugs-through` | `check-the-check` | a green suite with full line coverage and exact assertions gates merges: which real bugs in the code would still pass it? | 1 of 3 | — | only one side was run |
| `check-the-check-regression-test-misses-fix` | `check-the-check` | a PR fixes a bug and adds a regression test, CI is green: does that test prove the fix, or would it have passed before the fix too? | 3 of 3 | — | only one side was run |
| `check-the-check-tests-that-never-run` | `check-the-check` | release notes say a feature is covered by a green test file: do the tests that cover it ever run? | 3 of 3 | — | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran the skill's helper, scripts/verify.py or scripts/check.py):

| Case | Without skills | With skills |
|---|---|---|
| `check-the-check-green-gate-lets-bugs-through` | $0.14 · 42s · 6 turns · helper 0/3 | — |
| `check-the-check-regression-test-misses-fix` | $0.12 · 29s · 5 turns · helper 0/3 | — |
| `check-the-check-tests-that-never-run` | $0.08 · 19s · 4 turns · helper 0/3 | — |
| **all** | $0.12 · 30s · 5 turns · helper 0/9 | — |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
7 of 9 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

## Why tries failed

- `check-the-check-green-gate-lets-bugs-through` **without**: missed: the other amounts are pinned: changing the tax rate, the standard rate, or dropping the express add-on turns the suite red, so those parts of the gate do work
- `check-the-check-green-gate-lets-bugs-through` **without**: missed: the other amounts are pinned: changing the tax rate, the standard rate, or dropping the express add-on turns the suite red, so those parts of the gate do work

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
