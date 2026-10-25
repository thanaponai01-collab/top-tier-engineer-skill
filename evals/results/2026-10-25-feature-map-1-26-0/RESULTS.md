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

- **When:** 2026-10-25-1107
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 6
- **Plugin version:** 1.26.0
- **Cost of this run:** $8.40
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-feature-map-1-26-0/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `feature-map-crash-only-when-run` | `feature-map` | does the map of what the tool can do say what actually works when run, not only what the code declares, without destroying the person's notes to find out? | 3 of 3 | 2 of 6 | **skill hurts** |
| `feature-map-dead-command-and-destructive` | `feature-map` | is the map of what the tool can do true to the running code, with each way in proven or labelled, and nothing destroyed to prove it? | 3 of 3 | 6 of 6 | no difference — the agent already does this |
| `feature-map-map-survives-change` | `feature-map` | one session leaves a map of the CLI; a teammate then renames a command and breaks another so it only shows when run; a fresh session, with the same plain prompt and no skill in either arm, must bring the map up to date. Does what the first session left let the second find both, including the break that reads as correct? | 3 of 3 | 6 of 6 | no difference — the agent already does this |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `feature-map-crash-only-when-run` | $0.15 · 36s · 5 turns · verify.py 0/3 | $0.28 · 70s · 9 turns · verify.py 0/6 |
| `feature-map-dead-command-and-destructive` | $0.13 · 35s · 5 turns · verify.py 0/3 | $0.26 · 77s · 9 turns · verify.py 0/6 |
| `feature-map-map-survives-change` | $0.31 · 74s · 11 turns · verify.py 0/3 | $0.57 · 155s · 19 turns · verify.py 0/6 |
| **all** | $0.19 · 48s · 7 turns · verify.py 0/9 | $0.37 · 100s · 12 turns · verify.py 0/18 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
24 of 27 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 18 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `feature-map-crash-only-when-run` **with**: missed: purge deletes every note. The report says it was not run with --yes against the real notes.json: left unrun (traced from the code), or run only on a throwaway copy with the real notes untouched.
- `feature-map-crash-only-when-run` **with**: missed: purge deletes every note. The report says it was not run with --yes against the real notes.json: left unrun (traced from the code), or run only on a throwaway copy with the real notes untouched.
- `feature-map-crash-only-when-run` **with**: missed: purge deletes every note. The report says it was not run with --yes against the real notes.json: left unrun (traced from the code), or run only on a throwaway copy with the real notes untouched.; did not do it: a notes file maps add, list, search, tag, export and purge with notes.py as the way in, and notes.json still holds the three original notes (timed out)
- `feature-map-crash-only-when-run` **with**: did not do it: a notes file maps add, list, search, tag, export and purge with notes.py as the way in, and notes.json still holds the three original notes (timed out)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
