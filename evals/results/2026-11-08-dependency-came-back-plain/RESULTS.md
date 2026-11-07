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

- **When:** 2026-11-08-0103
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.44.0
- **Cost of this run:** $1.39
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.319 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-08-dependency-came-back-plain/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `dependency-health-came-back` | `dependency-health` | two sessions on the trip-itinerary app. Session 1 is the full dependency check (the same app and ask as dependency-health-owed-upgrades). Then a teammate's merge puts urllib3 1.24.1 (pulled in by requests, known holes) and PyYAML 5.3.1 (known hole) back into requirements.txt; requirements.in is untouched. Session 2 is bare (no plugin in either arm) and is asked only to add one package to the dependencies. Does what session 1 left behind make the second agent notice the two holed pins that came back, instead of compiling the new package in around them? | 0 of 3 | — | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `dependency-health-came-back` | $0.46 · 258s · 19 turns · verify.py 0/3 | — |
| **all** | $0.46 · 258s · 19 turns · verify.py 0/3 | — |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
0 of 3 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

## Why tries failed

- `dependency-health-came-back` **without**: missed: after the teammate's merge requirements.txt pins urllib3==1.24.1 again (via requests); the final report must name it as a security problem, fixed or not; missed: the merge also put PyYAML back to 5.3.1 (CVE-2020-14343); the final report must name it as a problem, fixed or not
- `dependency-health-came-back` **without**: missed: after the teammate's merge requirements.txt pins urllib3==1.24.1 again (via requests); the final report must name it as a security problem, fixed or not; missed: the merge also put PyYAML back to 5.3.1 (CVE-2020-14343); the final report must name it as a problem, fixed or not
- `dependency-health-came-back` **without**: missed: the merge also put PyYAML back to 5.3.1 (CVE-2020-14343); the final report must name it as a problem, fixed or not

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
