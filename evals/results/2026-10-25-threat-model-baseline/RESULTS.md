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

- **When:** 2026-10-25-1942
- **Model:** claude-opus-4-8, claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.32.0
- **Cost of this run:** $1.98
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-threat-model-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `threat-model-client-role-and-decoy` | `threat-model` | what can a signed-up customer account be made to do here? | 3 of 3 | — | only one side was run |
| `threat-model-general` | `threat-model` | general, not built around one trap: an ordinary storefront about to open signups; what can a customer account, or anyone, be made to do? | 3 of 3 | — | only one side was run |
| `threat-model-guard-not-applied` | `threat-model` | a staff-only guard that reads as applied: does the answer come from running the door or from reading it? | 3 of 3 | — | only one side was run |
| `threat-model-second-door` | `threat-model` | a customer reports one leaky door; is every door to the same data shut, and held by a test? | 3 of 3 | — | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `threat-model-client-role-and-decoy` | $0.11 · 30s · 4 turns · verify.py 0/3 | — |
| `threat-model-general` | $0.21 · 57s · 4 turns · verify.py 0/3 | — |
| `threat-model-guard-not-applied` | $0.20 · 52s · 4 turns · verify.py 0/3 | — |
| `threat-model-second-door` | $0.14 · 29s · 5 turns · verify.py 0/3 | — |
| **all** | $0.17 · 42s · 4 turns · verify.py 0/12 | — |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
6 of 12 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

## Why tries failed

None failed.

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
