# P01 expanded fresh-reader and upkeep trial

Date: 2026-10-13 (Asia/Bangkok)  
Model: `claude-sonnet-5-5`; plugin version: 4.61.1  
Scope: one bounded replay for each context arm, then one upkeep replay for each arm. This is a targeted expansion, not a reliability estimate.

## Fresh-reader context

The initial `project-context-task-trail` skill run passed its report (5/5), but its retained
`transcript.jsonl` shows `find brief evidence src work -type f` and opened unrelated-area content.
The initial control found 4/5 and missed the planted `src/billing/reconcile.py` shared caller.

I changed `skills/project-context/references/task-context.md` to require repository-scoped
exact-symbol searches and reading production callsites across areas before concluding a caller
list. The same fixture and task were replayed with and without the skill. Post-change, the skill
arm passed 5/5 and its transcript opened `src/billing/reconcile.py`, including the function and
call to `export_allowed`, without reading the planted unrelated record. The control again found
4/5 and missed only the planted shared-caller fact. This single run demonstrates the targeted
loading behavior on this fixture; it does not measure repeatability or general reliability.

Raw artifacts: `evals/results/pstack-next/project-context-task-trail/` (initial baseline) and
`evals/results/pstack-next-replay/project-context-task-trail/` (post-change replay). The earlier
failed Drive attempts and contracts remain separately retained at
`docs/RUN.pstack-next-initial-failed.json`, `docs/RUN.pstack-next-checker-failed.json`,
`work/pstack-next/contract.initial.json`, and `work/pstack-next/contract.v2.json`.

## Repeated upkeep

Both arms received the same local-fixture task and used the fixture's real `tools/context.py`.
Each arm indexed and checked the changed context records, captured Markdown bytes, repeated
index/check, and compared the snapshots. Both final comparisons exited zero with
`upkeep documents unchanged`; both reports passed 2/2. The skill arm loaded `project-update`.
No reads or searches escaped the fixture according to the retained transcript/action checks.

| Arm | Result | Cost | Time | Second-pass bytes |
|---|---:|---:|---:|---|
| With `project-update` | 2/2 passed | $0.0910 | 25.0 s | unchanged |
| Without skill | 2/2 passed | $0.0847 | 28.0 s | unchanged |

Raw artifacts: `evals/results/pstack-next-replay-v2/project-update-preserves-intent/{with,without}-1/`.
The point estimates come from one run per arm; they do not establish savings or a meaningful latency difference.

## Reproduction and scope

The retained behavior checker is `work/pstack-next/run_behavior_v4.py`; it reads the raw JSONL
tool transcripts and result records. Run `python work/pstack-next/run_behavior_v4.py` to recheck
those retained observations. Fixture integrity and prompt parity are checked by
`python work/pstack-next/check_fixture_v2.py`. The Drive content/proof gates and final run state
are recorded in `RUN.json`.

No release, plugin version change, or external publication was performed. Broader fresh-reader
and recovery reliability, repeated-run consistency, and upkeep savings remain unmeasured. Next:
use an independent larger-area fixture and selected repetitions with independently observed
actions; do not infer a full P01 acceptance from this bounded trial.
