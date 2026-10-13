# Scorecard — do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-13-1949
- **Model:** claude-sonnet-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 4.61.1
- **Cost of this run:** $0.17
- **Raw evidence:** `evals/results/p09-verified/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `drive-program-delivery` | `drive` | Does Drive turn a larger work graph and a dependent PR stack into bounded, current, non-mutating delivery guidance? | 0 of 1 | 1 of 1 | **skill helps** |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
1 of 2 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 1 of 1 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `drive-program-delivery` **without**: missed: C and D both write a persisted record, but no slice owns the shared storage layer, so parallel safety is not established until that boundary has an owner

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.

## P01 expanded fresh-reader and upkeep trial — 2026-10-13

Supplementary single-run evidence for the [PStack handoff trial](../work/pstack-next/evidence.md); it is not a multi-run scorecard or a reliability estimate. Model: claude-sonnet-5-5; plugin version 4.61.1.

| Trial | Without skill | With skill | Evidence |
|---|---|---|---|
| Fresh-reader baseline | 4/5; missed the shared caller and tripped the unrelated-area sweep | 5/5; passed report, but transcript broadly opened unrelated content | `results/pstack-next/project-context-task-trail/` |
| Fresh-reader after targeted search guidance | 4/5; same caller miss | 5/5; opened the production caller without unrelated content | `results/pstack-next-replay/project-context-task-trail/` |
| Repeated upkeep | 2/2; second local index/check left Markdown unchanged | 2/2; same byte-stability result, skill loaded | `results/pstack-next-replay-v2/project-update-preserves-intent/` |

The fresh-reader change targeted scoped symbol searches and production callsites across areas. Upkeep costs were $0.0847 without and $0.0910 with the skill (28.0s and 25.0s); one run per arm does not establish savings or a latency difference. Broader reliability remains unmeasured. Full details and failed-attempt records are linked from the evidence page.
