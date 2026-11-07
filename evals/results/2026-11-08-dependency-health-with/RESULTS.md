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

- **When:** 2026-11-08-0205
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.45.0
- **Cost of this run:** $2.25
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.319 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-08-dependency-health-with/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `dependency-health-came-back` | `dependency-health` | two sessions on the trip-itinerary app. Session 1 is the full dependency check (the same app and ask as dependency-health-owed-upgrades). Then a teammate's merge puts urllib3 1.24.1 (pulled in by requests, known holes) and PyYAML 5.3.1 (known hole) back into requirements.txt; requirements.in is untouched. Session 2 is bare (no plugin in either arm) and is asked only to add one package to the dependencies. Does what session 1 left behind make the second agent notice the two holed pins that came back, instead of compiling the new package in around them? | — | 0 of 3 | only one side was run |
| `dependency-health-owed-upgrades` | `dependency-health` | a small trip-itinerary app nobody has touched in a while, whose direct dependencies look current: the lockfile pins urllib3 1.24.1 under requests (known holes, only visible in the indirect pins), PyYAML 5.3.1 (a known hole the manifest allows), click is in requirements.in but missing from requirements.txt, simplejson is declared and imported by nothing, the Docker base is end-of-life Python 3.7, and Jinja2 2.11.3 has known holes but is pinned on purpose because the code uses contextfilter, which 3.1 removed. tzdata (needed by zoneinfo) and gunicorn (run by the Dockerfile) are imported by no Python file but are used. Does the agent find what is owed in the indirect pins and the lockfile, keep the two used packages, and not bump Jinja2 past the code? | — | 3 of 3 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `dependency-health-came-back` | — | $0.47 · 123s · 19 turns · verify.py 0/3 |
| `dependency-health-owed-upgrades` | — | $0.28 · 73s · 10 turns · verify.py 0/3 |
| **all** | — | $0.38 · 98s · 15 turns · verify.py 0/6 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
4 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 6 of 6 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `dependency-health-came-back` **with**: missed: after the teammate's merge requirements.txt pins urllib3==1.24.1 again (via requests); the final report must name it as a security problem, fixed or not; missed: the merge also put PyYAML back to 5.3.1 (CVE-2020-14343); the final report must name it as a problem, fixed or not
- `dependency-health-came-back` **with**: missed: after the teammate's merge requirements.txt pins urllib3==1.24.1 again (via requests); the final report must name it as a security problem, fixed or not; missed: the merge also put PyYAML back to 5.3.1 (CVE-2020-14343); the final report must name it as a problem, fixed or not
- `dependency-health-came-back` **with**: missed: after the teammate's merge requirements.txt pins urllib3==1.24.1 again (via requests); the final report must name it as a security problem, fixed or not

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
