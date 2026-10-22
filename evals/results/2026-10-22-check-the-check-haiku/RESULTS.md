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

- **When:** 2026-10-22-0739
- **Model:** claude-haiku-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.19.0
- **Cost of this run:** $0.18
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.304 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-22-check-the-check-haiku/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `check-the-check-ci-skips-a-test-file` | `check-the-check` | CI is green and the release notes say every item is covered: does the CI command even load the tests for each item? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `check-the-check-green-gate-lets-bugs-through` | `check-the-check` | a green suite with full line coverage and exact assertions gates merges: which real bugs in the code would still pass it? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `check-the-check-regression-test-misses-fix` | `check-the-check` | a PR fixes a bug and adds a regression test, CI is green: does that test prove the fix, or would it have passed before the fix too? | 3 of 3 | 3 of 3 | no difference — the agent already does this |
| `check-the-check-survivors-in-a-big-suite` | `check-the-check` | a 29-test suite with full statement coverage and boundary tests on most rules: does the agent find the two real bugs it lets through, buried among rules that are pinned? | 2 of 3 | 3 of 3 | skill seems to help — run more to be sure |
| `check-the-check-tests-that-never-run` | `check-the-check` | release notes say a feature is covered by a green test file: do the tests that cover it ever run? | 3 of 3 | 3 of 3 | no difference — the agent already does this |

**Cost per try** (mean $ · wall seconds · turns · tries that ran the skill's helper, scripts/verify.py or scripts/check.py):

| Case | Without skills | With skills |
|---|---|---|
| `check-the-check-ci-skips-a-test-file` | $0.01 · 22s · 8 turns · helper 0/3 | $0.01 · 25s · 8 turns · helper 3/3 |
| `check-the-check-green-gate-lets-bugs-through` | $0.01 · 43s · 6 turns · helper 0/3 | $0.01 · 47s · 8 turns · helper 3/3 |
| `check-the-check-regression-test-misses-fix` | $0.01 · 25s · 7 turns · helper 0/3 | $0.01 · 37s · 9 turns · helper 3/3 |
| `check-the-check-survivors-in-a-big-suite` | $0.01 · 48s · 8 turns · helper 0/3 | $0.01 · 29s · 9 turns · helper 3/3 |
| `check-the-check-tests-that-never-run` | $0.00 · 19s · 8 turns · helper 0/3 | $0.01 · 26s · 10 turns · helper 3/3 |
| **all** | $0.01 · 32s · 8 turns · helper 0/15 | $0.01 · 33s · 9 turns · helper 15/15 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
26 of 30 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 15 of 15 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `check-the-check-survivors-in-a-big-suite` **without**: missed: split_payment is never tested with a total that doesn't divide evenly: changing `base + 1` to `base - 1` (or `base + 2`) passes, so splitting 1000 three ways could return parts that add up to 998 and the gate stays green

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
