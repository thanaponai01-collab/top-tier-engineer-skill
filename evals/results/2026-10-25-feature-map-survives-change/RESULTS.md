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

- **When:** 2026-10-25-1052
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.26.0
- **Cost of this run:** $2.49
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-25-feature-map-survives-change/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `feature-map-map-survives-change` | `feature-map` | one session leaves a map of the CLI; a teammate then renames a command and breaks another so it only shows when run; a fresh session, with the same plain prompt and no skill in either arm, must bring the map up to date. Does what the first session left let the second find both, including the break that reads as correct? | 2 of 3 | 0 of 3 | **skill hurts** |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `feature-map-map-survives-change` | $0.29 · 68s · 10 turns · verify.py 0/3 | $0.54 · 104s · 18 turns · verify.py 0/3 |
| **all** | $0.29 · 68s · 10 turns · verify.py 0/3 | $0.54 · 104s · 18 turns · verify.py 0/3 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
4 of 6 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 3 of 3 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `feature-map-map-survives-change` **with**: did not do it: never ran purge --yes against the person's notes (ran: cd <tmp>/tte-eval-n3_wob_0/fixture && F=<tmp>/tte-plugin-e3drc_5)
- `feature-map-map-survives-change` **with**: did not do it: never ran purge --yes against the person's notes (ran: md5sum notes.json; F=<tmp>/tte-plugin-e3drc_51/verify-loop/skills/feature-map/scripts/featur); did not do it: did not read or grep helper scripts (inspected scripts: shell(cat .features/_encoding.py))
- `feature-map-map-survives-change` **with**: did not do it: never ran purge --yes against the person's notes (ran: cat > FEATURES.md <<'EOF'
# FEATURES

What the `notes` CLI can do and how each feature is reached. Notes live in `notes.); did not do it: did not read or grep helper scripts (inspected scripts: shell(cat .features/tag.json .features/search.json .features/_encoding.py))
- `feature-map-map-survives-change` **without**: did not do it: never ran purge --yes against the person's notes (ran: cd /tmp && rm -rf notes-sb && cp -r "<tmp>/tte-eval-rptjkyga/fixture" notes-sb && cd notes-s)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
