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

- **When:** 2026-10-25-1517
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.28.0
- **Cost of this run:** $2.77
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-wire-check-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `wire-check-alert-never-fires` | `wire-check` | a new event handler with three breaks in a row (module never loaded, wrong event name, wrong payload key whose TypeError the bus swallows); each fix only reveals the next. Does the agent make a real sale write the alert, and name every break? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-refund-already-wired` | `wire-check` | healthy control: the refund command is registered by a decorator in a module that pkgutil auto-loads, so billing.py never names it, and it works. Does the agent say so, with proof, and leave the code alone? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-what-nothing-reaches` | `wire-check` | whole-system: five unreached pieces, each broken at a different link (never registered, not scheduled, return value dropped, feature flag off, enabled only per deployment), beside decoys served by a second console script and a by-name job schedule. Does the agent classify each one and not call the served ones orphans? | 2 of 3 | 3 of 3 | skill seems to help — run more to be sure |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `wire-check-alert-never-fires` | $0.14 · 33s · 6 turns · verify.py 0/3 | $0.21 · 51s · 8 turns · verify.py 0/3 |
| `wire-check-refund-already-wired` | $0.09 · 21s · 5 turns · verify.py 0/3 | $0.13 · 29s · 5 turns · verify.py 0/3 |
| `wire-check-what-nothing-reaches` | $0.14 · 38s · 3 turns · verify.py 0/3 | $0.21 · 52s · 5 turns · verify.py 0/3 |
| **all** | $0.12 · 30s · 5 turns · verify.py 0/9 | $0.18 · 44s · 6 turns · verify.py 0/9 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
16 of 18 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 9 of 9 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `wire-check-what-nothing-reaches` **without**: fell for the trap: the receipt path is a lost effect; recommending deleting it as unused code misses the bug

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
