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

- **When:** 2026-11-07-2125
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.43.0
- **Cost of this run:** $1.18
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.319 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-07-checkup/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `checkup-ugly-but-idle` | `checkup` | a structural checkup that must rank by what costs the next change: the ugliest function is never changed, while a rule kept in two files keeps needing joint fixes and two HTTP clients each collect their own retry fixes | 0 of 3 | 3 of 3 | **skill helps** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `checkup-ugly-but-idle` | $0.15 · 37s · 4 turns · verify.py 0/3 | $0.25 · 56s · 9 turns · verify.py 0/3 |
| **all** | $0.15 · 37s · 4 turns · verify.py 0/3 | $0.25 · 56s · 9 turns · verify.py 0/3 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
3 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 3 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `checkup-ugly-but-idle` **without**: missed: HTTP is done two ways: shop/notify.py uses urllib.request and shop/payments.py uses http.client, each with its own retry and timeout loop, and each got its own fixes (email timeouts, webhook hammering, leaked connections); one shared client would take those fixes once
- `checkup-ugly-but-idle` **without**: missed: HTTP is done two ways: shop/notify.py uses urllib.request and shop/payments.py uses http.client, each with its own retry and timeout loop, and each got its own fixes (email timeouts, webhook hammering, leaked connections); one shared client would take those fixes once
- `checkup-ugly-but-idle` **without**: missed: the first thing to fix is the member/bulk discount rule kept twice, in shop/cart.py and shop/receipt.py, with no import between them; the git history shows them changing together and fixes for the receipt drifting from the cart (for example 'fix: receipt total differs from cart for members', 'fix: receipt and cart round the discount differently'). It must be ranked first, above the tax tables; missed: HTTP is done two ways: shop/notify.py uses urllib.request and shop/payments.py uses http.client, each with its own retry and timeout loop, and each got its own fixes (email timeouts, webhook hammering, leaked connections); one shared client would take those fixes once

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
