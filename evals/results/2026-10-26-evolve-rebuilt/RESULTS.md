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

- **When:** 2026-10-26-0210
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.33.0
- **Cost of this run:** $1.41
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-26-evolve-rebuilt/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `evolve-maintain-distant-break` | `evolve-maintain` | asked to cache Order.total, does the agent keep the features far from the model working: a refund that appends to order.lines directly, and a backup that dumps every attribute with default=vars and restores with Order(**d)? | — | 3 of 3 | only one side was run |
| `evolve-maintain-hidden-caller` | `evolve-maintain` | before removing a deprecated endpoint, are all its callers found, including ones outside the code, and moved first? | — | 3 of 3 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `evolve-maintain-distant-break` | — | $0.22 · 59s · 7 turns · verify.py 0/3 |
| `evolve-maintain-hidden-caller` | — | $0.25 · 70s · 10 turns · verify.py 0/3 |
| **all** | — | $0.23 · 64s · 8 turns · verify.py 0/6 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
5 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 6 of 6 tries.
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
