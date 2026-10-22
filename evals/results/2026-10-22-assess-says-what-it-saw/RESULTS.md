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

- **When:** 2026-10-22-1429
- **Model:** claude-opus-5-5, claude-sonnet-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.18.2
- **Cost of this run:** $3.50
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.300 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-22-assess-says-what-it-saw/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `verify-loop-compound-advance` | `verify-loop` | asked to advance settlement and fee calculations into verified status: does the finished repo repair hollow checks, map unmapped fee logic, fix bugs, record fail-proof receipts, and freeze a strict green baseline? | 0 of 3 | 2 of 3 | **skill helps** |
| `verify-loop-compound-assess` | `verify-loop` | auditing verification health across billing, discounts, tax, and shipping: does the agent catch the hollow tax check, loosened invoice check hiding per-line floor bug, coupon cap mutation survivor, unmapped rebate module, while recognizing shipping is healthy? | 0 of 3 | 2 of 3 | **skill helps** |
| `verify-loop-fake-check-and-decoy` | `verify-loop` | the suite is green — does that prove the discount code works? | 3 of 3 | 2 of 3 | **skill hurts** |
| `verify-loop-green-with-unverified` | `verify-loop` | the run is green: is every feature verified, as the release notes will claim? | 0 of 3 | 3 of 3 | **skill helps** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `verify-loop-compound-advance` | $0.12 · 26s · 5 turns · verify.py 0/3 | $0.32 · 66s · 13 turns · verify.py 3/3 |
| `verify-loop-compound-assess` | $0.07 · 32s · 8 turns · verify.py 0/3 | $0.19 · 44s · 7 turns · verify.py 3/3 |
| `verify-loop-fake-check-and-decoy` | $0.08 · 24s · 4 turns · verify.py 0/3 | $0.14 · 30s · 6 turns · verify.py 3/3 |
| `verify-loop-green-with-unverified` | $0.07 · 16s · 3 turns · verify.py 0/3 | $0.17 · 38s · 8 turns · verify.py 3/3 |
| **all** | $0.09 · 25s · 5 turns · verify.py 0/12 | $0.20 · 45s · 8 turns · verify.py 12/12 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
9 of 24 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 12 of 12 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

**Did the agent follow the skill's own steps?** Scored apart from the table above, because
only the side with skills can be asked it:
- `verify-loop-compound-advance`: 3 of 3 tries — executed helper subcommands: advance, answer-check.
- `verify-loop-compound-assess`: 3 of 3 tries — executed helper subcommands: assess, answer-check.

## Why tries failed

- `verify-loop-compound-advance` **with**: missed: fee.py is unmapped in VERIFY.md and test_fee.py is an orphan test not tracked by any verification contract
- `verify-loop-compound-advance` **without**: did not do it: VERIFY.md has a fail-proof line recording the failure proof receipt (VERIFY.md has nothing matching '(?im)^\\s*-\\s*fail-proof:\\s*\\S.{10,}'); did not do it: the finished checks were frozen with verify.py baseline (.verify-state.json is not there); did not do it: final helper status is strict, current and green (VERIFY-STATE: never-run (VERIFY.md exists, no run recorded))
- `verify-loop-compound-advance` **without**: did not do it: VERIFY.md has a fail-proof line recording the failure proof receipt (VERIFY.md has nothing matching '(?im)^\\s*-\\s*fail-proof:\\s*\\S.{10,}'); did not do it: the finished checks were frozen with verify.py baseline (.verify-state.json is not there); did not do it: final helper status is strict, current and green (VERIFY-STATE: never-run (VERIFY.md exists, no run recorded))
- `verify-loop-compound-advance` **without**: did not do it: VERIFY.md has a fail-proof line recording the failure proof receipt (VERIFY.md has nothing matching '(?im)^\\s*-\\s*fail-proof:\\s*\\S.{10,}'); did not do it: the finished checks were frozen with verify.py baseline (.verify-state.json is not there); did not do it: the copy's own tests pass when fee.py is correct (exit 1, expected 0); did not do it: final helper status is strict, current and green (VERIFY-STATE: never-run (VERIFY.md exists, no run recorded))
- `verify-loop-compound-assess` **with**: missed: agent-1's commit introduced a per-line rounding bug in invoice.py that rounds down each line before summing instead of rounding the total half-up, passing only because delta=2 absorbs the discrepancy
- `verify-loop-compound-assess` **without**: missed: the Coupons contract has no path: in VERIFY.md; mutation analysis surveys coupons.py and finds mutations to the 5000-cent cap survive because test_coupons.py only tests small discounts
- `verify-loop-compound-assess` **without**: missed: the Coupons contract has no path: in VERIFY.md; mutation analysis surveys coupons.py and finds mutations to the 5000-cent cap survive because test_coupons.py only tests small discounts
- `verify-loop-compound-assess` **without**: missed: the Coupons contract has no path: in VERIFY.md; mutation analysis surveys coupons.py and finds mutations to the 5000-cent cap survive because test_coupons.py only tests small discounts; missed: agent-1's commit introduced a per-line rounding bug in invoice.py that rounds down each line before summing instead of rounding the total half-up, passing only because delta=2 absorbs the discrepancy
- `verify-loop-fake-check-and-decoy` **with**: missed: breaking apply_discount (e.g. 0.9 -> 0.8) leaves test_save10_discount green, proving the check is fake
- `verify-loop-green-with-unverified` **without**: missed: the checks that do exist were never shown able to go red: no fail-proof lines
- `verify-loop-green-with-unverified` **without**: missed: the checks that do exist were never shown able to go red: no fail-proof lines
- `verify-loop-green-with-unverified` **without**: missed: the checks that do exist were never shown able to go red: no fail-proof lines

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
