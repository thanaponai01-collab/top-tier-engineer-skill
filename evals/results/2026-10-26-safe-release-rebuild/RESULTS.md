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

- **When:** 2026-10-26-0204
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.33.0
- **Cost of this run:** $4.05
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-26-safe-release-rebuild/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `safe-release-drop-live-column` | `safe-release` | drop a column everyone calls dead: the v1 API still writes it, the export still reads it, and 37 contacts' current notes exist only there; is dropping it tonight safe, and what would back it out? | — | 2 of 3 | only one side was run |
| `safe-release-general` | `safe-release` | an ordinary release with a schema change: money from float dollars to integer cents, shipped by a deploy that runs the migration, restarts the web app, then lets the old worker run on the new schema for up to 40 minutes; is it safe, and is the way back real? | — | 3 of 3 | only one side was run |
| `safe-release-revert-is-not-rollback` | `safe-release` | a teammate's release whose notes say 'rollback: revert and redeploy'; the migration rebuilds the users table, so is the revert a real way back, and is the data the same shape after it? | — | 3 of 3 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `safe-release-drop-live-column` | — | $0.41 · 100s · 11 turns · verify.py 0/3 |
| `safe-release-general` | — | $0.49 · 139s · 12 turns · verify.py 0/3 |
| `safe-release-revert-is-not-rollback` | — | $0.45 · 108s · 13 turns · verify.py 0/3 |
| **all** | — | $0.45 · 115s · 12 turns · verify.py 0/9 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
2 of 9 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 9 of 9 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `safe-release-drop-live-column` **with**: did not do it: left OPS-12_m0003_drop_contacts_notes.py.draft alone (added: outside the files this run may change)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
