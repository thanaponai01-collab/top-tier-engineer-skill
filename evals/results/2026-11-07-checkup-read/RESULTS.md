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

- **When:** 2026-11-07-2254
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.43.0
- **Cost of this run:** $1.39
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.319 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-07-checkup-read/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `checkup-ugly-but-idle` | `checkup` | a structural checkup that must rank by what costs the next change: the ugliest function is never changed, while a rule kept in two files keeps needing joint fixes and two HTTP clients each collect their own retry fixes; and the code holds two bugs no structure measure sees, which a reader of the code finds and a report that stays inside its sections misses | 1 of 3 | 2 of 3 | skill seems to help — run more to be sure |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `checkup-ugly-but-idle` | $0.15 · 32s · 4 turns · verify.py 0/3 | $0.32 · 74s · 10 turns · verify.py 0/3 |
| **all** | $0.15 · 32s · 4 turns · verify.py 0/3 | $0.32 · 74s · 10 turns · verify.py 0/3 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
2 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `checkup-ugly-but-idle` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-qd4x1vh8/verify-loop/ski), shell(sed -n 578,610p /c/Users/)
- `checkup-ugly-but-idle` **without**: missed: HTTP is done two ways: shop/notify.py uses urllib.request and shop/payments.py uses http.client, each with its own retry and timeout loop, and each got its own fixes (email timeouts, webhook hammering, leaked connections); one shared client would take those fixes once
- `checkup-ugly-but-idle` **without**: missed: HTTP is done two ways: shop/notify.py uses urllib.request and shop/payments.py uses http.client, each with its own retry and timeout loop, and each got its own fixes (email timeouts, webhook hammering, leaked connections); one shared client would take those fixes once

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
