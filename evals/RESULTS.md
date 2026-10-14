# Scorecard — do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-14-2156
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 4.64.1 (run before the 4.65.0 bump; the skill text matched except its added *Test:* line)
- **Cost of this run:** $1.93
- **Raw evidence:** `evals/results/2026-10-14-surplus/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `surplus-finds-real-work` | `surplus` | given spare budget and no goal, does it find what only running things reveals (a README claim the code breaks, a test that fails one run in five, correct code whose boundaries no test pins) instead of busywork, and leave checks that catch each? | 0 of 3 | 3 of 3 | **skill helps** |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
3 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 2 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `surplus-finds-real-work` **without**: missed: no test pins the free-shipping boundary: changing >= 50 to > 50 in shipping_cost leaves the suite green, so a 50.00 order could start paying 4.95 unnoticed; missed: tier() is correct but no test sits on either threshold: changing >= 1000 or >= 250 to > leaves the suite green, so a customer at exactly 1000 or 250 points could silently drop a tier; missed: can_return() is correct but no test sits on day 30: changing <= 30 to < 30 leaves the suite green, so the last day of the window could silently stop accepting returns; did not do it: the copy's suite goes red when shipping_cost uses > 50 instead of >= 50 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes gold start above 1000 instead of at 1000 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes silver start above 250 instead of at 250 (exit 0, expected non-zero); did not do it: the copy's suite goes red when can_return() closes the window before day 30 (exit 0, expected non-zero)
- `surplus-finds-real-work` **without**: missed: no test pins the free-shipping boundary: changing >= 50 to > 50 in shipping_cost leaves the suite green, so a 50.00 order could start paying 4.95 unnoticed; missed: tier() is correct but no test sits on either threshold: changing >= 1000 or >= 250 to > leaves the suite green, so a customer at exactly 1000 or 250 points could silently drop a tier; missed: can_return() is correct but no test sits on day 30: changing <= 30 to < 30 leaves the suite green, so the last day of the window could silently stop accepting returns; did not do it: the copy's suite goes red when shipping_cost uses > 50 instead of >= 50 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes gold start above 1000 instead of at 1000 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes silver start above 250 instead of at 250 (exit 0, expected non-zero); did not do it: the copy's suite goes red when can_return() closes the window before day 30 (exit 0, expected non-zero)
- `surplus-finds-real-work` **without**: missed: no test pins the free-shipping boundary: changing >= 50 to > 50 in shipping_cost leaves the suite green, so a 50.00 order could start paying 4.95 unnoticed; missed: tier() is correct but no test sits on either threshold: changing >= 1000 or >= 250 to > leaves the suite green, so a customer at exactly 1000 or 250 points could silently drop a tier; missed: can_return() is correct but no test sits on day 30: changing <= 30 to < 30 leaves the suite green, so the last day of the window could silently stop accepting returns; did not do it: the copy's suite goes red when shipping_cost uses > 50 instead of >= 50 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes gold start above 1000 instead of at 1000 (exit 0, expected non-zero); did not do it: the copy's suite goes red when tier() makes silver start above 250 instead of at 250 (exit 0, expected non-zero); did not do it: the copy's suite goes red when can_return() closes the window before day 30 (exit 0, expected non-zero)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.
