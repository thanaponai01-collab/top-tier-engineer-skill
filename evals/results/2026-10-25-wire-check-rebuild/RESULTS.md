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

- **When:** 2026-10-25-1554
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.29.0
- **Cost of this run:** $9.10
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-wire-check-rebuild/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `wire-check-alarm-on-narrow-task` | `wire-check` | a narrow follow-up task: one session repairs the low-stock alert; a teammate then moves `import app.handlers` into `restock` only, so a sale fires no handler at all, while a test that imports the handlers itself still passes; a fresh session, same plain prompt and no skill in either arm, is asked only to document the alert. Does what the first session left raise the alarm that a sale no longer alerts? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-alert-never-fires` | `wire-check` | a new event handler with three breaks in a row (module never loaded, wrong event name, wrong payload key whose TypeError the bus swallows); each fix only reveals the next. Does the agent make a real sale write the alert, and name every break? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-refund-already-wired` | `wire-check` | healthy control: the refund command is registered by a decorator in a module that pkgutil auto-loads, so billing.py never names it, and it works. Does the agent say so, with proof, and leave the code alone? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-too-big-to-read` | `wire-check` | whole-system on a CLI too big to read in one go (390 files, 364 auto-registered commands, ~940 functions): six unreached pieces, three of them single functions inside live files, beside decoys a static reading gets wrong (commands found by pkgutil, exporters loaded by name, a handler whose event is published through an f-string). Does the agent find all six and spare the decoys? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `wire-check-what-nothing-reaches` | `wire-check` | whole-system: five unreached pieces, each broken at a different link (never registered, not scheduled, return value dropped, feature flag off, enabled only per deployment), beside decoys served by a second console script and a by-name job schedule. Does the agent classify each one and not call the served ones orphans? | 3 of 3 | 3 of 3 | no difference — the agent already does this |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `wire-check-alarm-on-narrow-task` | $0.23 · 58s · 10 turns · verify.py 0/3 | $0.78 · 166s · 26 turns · verify.py 3/3 |
| `wire-check-alert-never-fires` | $0.12 · 27s · 5 turns · verify.py 0/3 | $0.59 · 140s · 19 turns · verify.py 3/3 |
| `wire-check-refund-already-wired` | $0.09 · 21s · 4 turns · verify.py 0/3 | $0.12 · 23s · 5 turns · verify.py 0/3 |
| `wire-check-too-big-to-read` | $0.27 · 143s · 9 turns · verify.py 0/3 | $0.43 · 425s · 14 turns · verify.py 0/3 |
| `wire-check-what-nothing-reaches` | $0.13 · 35s · 3 turns · verify.py 0/3 | $0.27 · 65s · 9 turns · verify.py 0/3 |
| **all** | $0.17 · 57s · 6 turns · verify.py 0/15 | $0.44 · 164s · 15 turns · verify.py 6/15 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
28 of 30 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 15 of 15 tries.
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
