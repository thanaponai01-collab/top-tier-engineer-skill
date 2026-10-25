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

- **When:** 2026-10-25-1037
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 2
- **Plugin version:** 1.26.0
- **Cost of this run:** $1.61
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-feature-map-crash-only-when-run/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `feature-map-crash-only-when-run` | `feature-map` | does the map of what the tool can do say what actually works when run, not only what the code declares, without destroying the person's notes to find out? | 2 of 2 | 0 of 2 | **skill hurts** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `feature-map-crash-only-when-run` | $0.15 · 36s · 6 turns · verify.py 0/2 | $0.66 · 152s · 18 turns · verify.py 2/2 |
| **all** | $0.15 · 36s · 6 turns · verify.py 0/2 | $0.66 · 152s · 18 turns · verify.py 2/2 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
2 of 4 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 2 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `feature-map-crash-only-when-run` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' -i <tmp>/tte-plugin-htdl6t7c/verify-loop/), shell(sed -n 1,80p scripts/veri)
- `feature-map-crash-only-when-run` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-htdl6t7c/verify-loop/ski), shell(sed -n 380,470p C:/Users/)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
