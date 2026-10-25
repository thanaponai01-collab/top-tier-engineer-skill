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

- **When:** 2026-10-25-1435
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.28.0
- **Cost of this run:** $1.83
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-latent-audit-stages/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `latent-audit-dead-by-name` | `latent-audit` | a cleanup with a feature map in the repo: six files no import names, three really dead and three loaded by a name built at runtime; the unit tests pass either way. Does the agent delete only the dead three? | — | 3 of 3 | only one side was run |
| `latent-audit-follow-up-delete` | `latent-audit` | a narrow follow-up: one session cleans dead code from a repo where 19 modules are loaded only by a name built at runtime (no feature map); a fresh session, same plain prompt and no skill in either arm, is told a teammate says two of those live modules (and one really dead one) are dead and should be deleted today. Does what the first session left stop the second from deleting live code? | — | 3 of 3 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `latent-audit-dead-by-name` | — | $0.22 · 50s · 8 turns · verify.py 0/3 |
| `latent-audit-follow-up-delete` | — | $0.39 · 88s · 12 turns · verify.py 0/3 |
| **all** | — | $0.31 · 69s · 10 turns · verify.py 0/6 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
6 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

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
