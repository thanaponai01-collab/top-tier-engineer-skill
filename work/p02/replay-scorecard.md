# Scorecard â€” do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-13-1232
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 4.61.1
- **Cost of this run:** $0.26
- **Raw evidence:** `evals/results/p02-replay/` â€” every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `verify-loop-make-it-verified` | `verify-loop` | asked to get refunds verified, does the finished repo hold a check that can tell broken code from correct code, with the proof recorded and the check frozen? | â€” | 0 of 1 | only one side was run |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
1 of 1 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 1 of 1 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `verify-loop-make-it-verified` **with**: did not do it: the finished checks were frozen with verify.py baseline (.verify-state.json has nothing matching '"baseline"\\s*:\\s*\\{\\s*"[^"]'); did not do it: final helper status is strict, current and green (VERIFY-STATE: red (red run 1 in a row))

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference â€” the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.
