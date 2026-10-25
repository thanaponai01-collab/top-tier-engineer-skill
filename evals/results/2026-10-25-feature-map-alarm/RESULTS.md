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

- **When:** 2026-10-25-1204
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.26.0
- **Cost of this run:** $3.85
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-feature-map-alarm/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `feature-map-alarm-on-narrow-task` | `feature-map` | a narrow follow-up task: one session maps a 133-command CLI; a teammate renames `show-mood` and, unmentioned, breaks three obscure commands so it only shows when they run; a fresh session, same plain prompt and no skill in either arm, is asked only to update the docs for the rename. Does what the first session left raise the alarm on the breaks nobody asked about? | 0 of 3 | 3 of 3 | **skill helps** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `feature-map-alarm-on-narrow-task` | $0.39 · 71s · 13 turns · verify.py 0/3 | $0.89 · 302s · 24 turns · verify.py 0/3 |
| **all** | $0.39 · 71s · 13 turns · verify.py 0/3 | $0.89 · 302s · 24 turns · verify.py 0/3 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
6 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `feature-map-alarm-on-narrow-task` **without**: missed: the rating range check in commands/fields/rating.py (parse, shared by `set-rating` and `by-rating`) is inverted, so every valid rating is refused: `set-rating 1 4` or `by-rating 4` exits 1 with 'rating must be 1-5'. Naming either command counts. Nobody asked about it: the report must raise it unprompted.; missed: `count-owner` raises TypeError (str vs None in its sort) because a note has no owner. Nobody asked about it: the report must raise it unprompted.; missed: `clear-sprint` raises KeyError: 'sprint' after popping the field into history and then printing it. Nobody asked about it: the report must raise it unprompted.; did not do it: a notes file in the repo maps the 133-command CLI including `mood`, and notes.json still holds the three original notes (exit 1, expected 0)
- `feature-map-alarm-on-narrow-task` **without**: missed: the rating range check in commands/fields/rating.py (parse, shared by `set-rating` and `by-rating`) is inverted, so every valid rating is refused: `set-rating 1 4` or `by-rating 4` exits 1 with 'rating must be 1-5'. Naming either command counts. Nobody asked about it: the report must raise it unprompted.; missed: `count-owner` raises TypeError (str vs None in its sort) because a note has no owner. Nobody asked about it: the report must raise it unprompted.; missed: `clear-sprint` raises KeyError: 'sprint' after popping the field into history and then printing it. Nobody asked about it: the report must raise it unprompted.; did not do it: a notes file in the repo maps the 133-command CLI including `mood`, and notes.json still holds the three original notes (exit 1, expected 0)
- `feature-map-alarm-on-narrow-task` **without**: missed: the rating range check in commands/fields/rating.py (parse, shared by `set-rating` and `by-rating`) is inverted, so every valid rating is refused: `set-rating 1 4` or `by-rating 4` exits 1 with 'rating must be 1-5'. Naming either command counts. Nobody asked about it: the report must raise it unprompted.; missed: `count-owner` raises TypeError (str vs None in its sort) because a note has no owner. Nobody asked about it: the report must raise it unprompted.; missed: `clear-sprint` raises KeyError: 'sprint' after popping the field into history and then printing it. Nobody asked about it: the report must raise it unprompted.; did not do it: a notes file in the repo maps the 133-command CLI including `mood`, and notes.json still holds the three original notes (exit 1, expected 0)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
