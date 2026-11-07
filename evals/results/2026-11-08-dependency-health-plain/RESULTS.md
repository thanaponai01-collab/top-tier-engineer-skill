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

- **When:** 2026-11-08-0052
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.44.0
- **Cost of this run:** $0.73
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.319 (Claude Code)
- **Raw evidence:** `evals/results/2026-11-08-dependency-health-plain/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `dependency-health-owed-upgrades` | `dependency-health` | a small trip-itinerary app nobody has touched in a while, whose direct dependencies look current: the lockfile pins urllib3 1.24.1 under requests (known holes, only visible in the indirect pins), PyYAML 5.3.1 (a known hole the manifest allows), click is in requirements.in but missing from requirements.txt, simplejson is declared and imported by nothing, the Docker base is end-of-life Python 3.7, and Jinja2 2.11.3 has known holes but is pinned on purpose because the code uses contextfilter, which 3.1 removed. tzdata (needed by zoneinfo) and gunicorn (run by the Dockerfile) are imported by no Python file but are used. Does the agent find what is owed in the indirect pins and the lockfile, keep the two used packages, and not bump Jinja2 past the code? | 2 of 3 | — | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `dependency-health-owed-upgrades` | $0.24 · 83s · 8 turns · verify.py 0/3 | — |
| **all** | $0.24 · 83s · 8 turns · verify.py 0/3 | — |

## Why tries failed

- `dependency-health-owed-upgrades` **without**: missed: simplejson is declared and pinned but no file imports it (rates.py uses the standard json module); the report must say it is unused

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
