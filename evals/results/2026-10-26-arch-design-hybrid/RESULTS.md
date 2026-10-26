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

- **When:** 2026-10-26-0259
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.34.0
- **Cost of this run:** $8.72
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-26-arch-design-hybrid/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `arch-design-competing-candidates` | `arch-design` | does the design expose and compare bounded structural options for a consequential fork? | — | 2 of 3 | only one side was run |
| `arch-design-graph-shape` | `arch-design` | where is the shape costing change, and what is the top move? | — | 1 of 3 | only one side was run |
| `arch-design-no-new-store` | `arch-design` | how should CSV export and its history be structured, and which decision here is expensive to get wrong? | — | 1 of 3 | only one side was run |
| `arch-design-one-owner` | `arch-design` | where did the structure go wrong, and what is the top move? | — | 3 of 3 | only one side was run |
| `arch-design-routine` | `arch-design` | does routine settled work stay direct without competing-design ceremony? | — | 3 of 3 | only one side was run |
| `arch-design-stale-map-owner-view` | `arch-design` | for an owner who can't read code: what is wrong, what better looks like, and does the review trust a stale map? | — | 0 of 3 | only one side was run |
| `arch-design-verify-caller-count` | `arch-design` | is the shipping seam safe to inline, and what changes if so? | — | 2 of 3 | only one side was run |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `arch-design-competing-candidates` | — | $0.30 · 69s · 8 turns · verify.py 0/3 |
| `arch-design-graph-shape` | — | $0.68 · 186s · 14 turns · verify.py 0/3 |
| `arch-design-no-new-store` | — | $0.45 · 118s · 13 turns · verify.py 0/3 |
| `arch-design-one-owner` | — | $0.31 · 77s · 10 turns · verify.py 0/3 |
| `arch-design-routine` | — | $0.12 · 28s · 5 turns · verify.py 0/3 |
| `arch-design-stale-map-owner-view` | — | $0.75 · 197s · 19 turns · verify.py 0/3 |
| `arch-design-verify-caller-count` | — | $0.29 · 71s · 10 turns · verify.py 0/3 |
| **all** | — | $0.42 · 107s · 11 turns · verify.py 0/21 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
5 of 21 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 21 of 21 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `arch-design-competing-candidates` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' -i <tmp>/tte-plugin-xyuh7tpb/verify-loop/))
- `arch-design-graph-shape` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' tte-plugin-xyuh7tpb/verify-loop/skills/arch-design/scripts/arch.py | ))
- `arch-design-graph-shape` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-xyuh7tpb/verify-loop/ski))
- `arch-design-no-new-store` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-xyuh7tpb/verify-loop/ski))
- `arch-design-no-new-store` **with**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database; did not do it: did not read or grep helper scripts (inspected scripts: shell(sed -n 1,80p <tmp>/tte-plugin-xyuh7tpb/verify-loop/s), shell(grep -n '' <home>)
- `arch-design-stale-map-owner-view` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-xyuh7tpb/verify-loop/ski))
- `arch-design-stale-map-owner-view` **with**: missed: the owner is shown today's flow and the better flow as pictures (diagrams or a visual report), side by side or one after the other, not only prose; did not do it: did not read or grep helper scripts (inspected scripts: shell(sed -n 225,300p <tmp>/tte-plugin-xyuh7tpb/verify-loo), shell(sed -n 436,470p /c/Users/)
- `arch-design-stale-map-owner-view` **with**: missed: the owner is shown today's flow and the better flow as pictures (diagrams or a visual report), side by side or one after the other, not only prose; did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-xyuh7tpb/verify-loop/ski))
- `arch-design-verify-caller-count` **with**: did not do it: did not read or grep helper scripts (inspected scripts: shell(grep -n '' <tmp>/tte-plugin-xyuh7tpb/verify-loop/ski))

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
