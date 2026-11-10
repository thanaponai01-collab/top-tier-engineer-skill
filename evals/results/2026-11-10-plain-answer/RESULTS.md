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

- **When:** 2026-11-10-1143
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 1.49.0
- **Cost of this run:** $0.33
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.322 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-10-plain-answer/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `state-machines-print-shop` | `state-machines` | a print-shop app whose order status, print job flags and customer notify flags are three implicit state machines. Four bugs are planted: refund checks for "canceled" while cancel writes "cancelled", the nightly job expires orders that are "pending", a state nothing sets, a printer jam leaves the job flagged printing forever, and ship() moves any order to shipped. Two things look like bugs but are not: the notify flags are independent and every combination is valid, and archive() is guarded by a decorator. Does the agent find all four, leave the two alone, and fix the four without breaking anything? | — | 1 of 1 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `state-machines-print-shop` | — | $0.33 · 75s · 9 turns · verify.py 0/1 |
| **all** | — | $0.33 · 75s · 9 turns · verify.py 0/1 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
1 of 1 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 1 of 1 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

None failed.

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
