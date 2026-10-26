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

- **When:** 2026-10-26-0148
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 1.33.0
- **Cost of this run:** $2.54
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-26-arch-design-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `arch-design-competing-candidates` | `arch-design` | does the design expose and compare bounded structural options for a consequential fork? | 0 of 1 | 1 of 1 | **skill helps** |
| `arch-design-graph-shape` | `arch-design` | where is the shape costing change, and what is the top move? | 0 of 1 | 1 of 1 | **skill helps** |
| `arch-design-no-new-store` | `arch-design` | how should CSV export and its history be structured, and which decision here is expensive to get wrong? | 0 of 1 | 1 of 1 | **skill helps** |
| `arch-design-one-owner` | `arch-design` | where did the structure go wrong, and what is the top move? | 0 of 1 | 1 of 1 | **skill helps** |
| `arch-design-routine` | `arch-design` | does routine settled work stay direct without competing-design ceremony? | 1 of 1 | 1 of 1 | no difference — the agent already does this |
| `arch-design-stale-map-owner-view` | `arch-design` | for an owner who can't read code: what is wrong, what better looks like, and does the review trust a stale map? | 1 of 1 | 1 of 1 | no difference — the agent already does this |
| `arch-design-verify-caller-count` | `arch-design` | is the shipping seam safe to inline, and what changes if so? | 1 of 1 | 1 of 1 | no difference — the agent already does this |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `arch-design-competing-candidates` | $0.10 · 29s · 2 turns · verify.py 0/1 | $0.18 · 57s · 4 turns · verify.py 0/1 |
| `arch-design-graph-shape` | $0.22 · 54s · 4 turns · verify.py 0/1 | $0.33 · 106s · 6 turns · verify.py 0/1 |
| `arch-design-no-new-store` | $0.11 · 32s · 3 turns · verify.py 0/1 | $0.34 · 94s · 8 turns · verify.py 0/1 |
| `arch-design-one-owner` | $0.09 · 23s · 3 turns · verify.py 0/1 | $0.25 · 60s · 7 turns · verify.py 0/1 |
| `arch-design-routine` | $0.05 · 12s · 2 turns · verify.py 0/1 | $0.09 · 22s · 3 turns · verify.py 0/1 |
| `arch-design-stale-map-owner-view` | $0.11 · 33s · 3 turns · verify.py 0/1 | $0.41 · 111s · 7 turns · verify.py 0/1 |
| `arch-design-verify-caller-count` | $0.09 · 22s · 3 turns · verify.py 0/1 | $0.17 · 42s · 5 turns · verify.py 0/1 |
| **all** | $0.11 · 29s · 3 turns · verify.py 0/7 | $0.25 · 70s · 6 turns · verify.py 0/7 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
8 of 14 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 7 of 7 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `arch-design-competing-candidates` **without**: missed: sets decision criteria before evaluating designs, including duplicate-refund safety, operator status, latency/retry behavior, and operating cost; missed: shows distinct synchronous existing-service and durable asynchronous queue/outbox designs, rather than renaming one shape
- `arch-design-graph-shape` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not change
- `arch-design-no-new-store` **without**: missed: app/db.py is already the single place reports/models.py and users/models.py persist through; export history belongs there, not in new storage; missed: only CSV is asked for, so the design is one function against stdlib csv, not an exporter interface, registry or plugin seam built for formats nobody has asked for; missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
