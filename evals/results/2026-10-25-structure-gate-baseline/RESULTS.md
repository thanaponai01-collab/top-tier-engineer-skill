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

- **When:** 2026-10-25-1904
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.31.0
- **Cost of this run:** $1.27
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-structure-gate-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `structure-gate-general` | `structure-gate` | general, not built around one trap: an ordinary small invoicing app with one tangled function, an import cycle, a copied block and otherwise small modules; is it a mess, and where? | 3 of 3 | — | only one side was run |
| `structure-gate-opaque-not-clean` | `structure-gate` | three tiny functions — is it clean? | 0 of 3 | 3 of 3 | **skill helps** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `structure-gate-general` | $0.16 · 46s · 5 turns · verify.py 0/3 | — |
| `structure-gate-opaque-not-clean` | $0.10 · 17s · 3 turns · verify.py 0/3 | $0.17 · 36s · 6 turns · verify.py 0/3 |
| **all** | $0.13 · 32s · 4 turns · verify.py 0/6 | $0.17 · 36s · 6 turns · verify.py 0/3 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
6 of 9 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict
- `structure-gate-opaque-not-clean` **without**: missed: dashboard.py holds 230 lines of JavaScript inside a string literal that no parser, linter or test can enter; missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
