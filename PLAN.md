# PStack fresh-reader and upkeep follow-up

Exit check: `python work/pstack-next/run_behavior_v4.py` confirms a transcript-backed difference on scoped fresh-reader loading, plus a repeated local index/check pass with unchanged Markdown; `python work/pstack-next/prove.py` passes tests and catalog.

| Slice | Files | Check | Depends on |
|---|---|---|---|
| Bound the fixtures | `evals/cases/project-context-task-trail/`, `evals/cases/project-update-preserves-intent/`, `work/pstack-next/check_fixture_v2.py` | Larger fixture, actual shared caller/helper, control and skill prompts match, external paths are forbidden | none |
| Close the retrieval gap and repeat upkeep | `skills/project-context/references/task-context.md`, `work/pstack-next/run_behavior_v4.py` | Transcript-backed action/output comparison; skill reads caller without unrelated area content; both upkeep arms repeat helper and preserve Markdown bytes | fixtures |
| Record and prove | `work/pstack-next/evidence.md`, `work/pstack-handoff.md`, `BUILD.md`, `evals/RESULTS.md` | Content gate, full suite, catalog | behavior |

The first expanded attempt exposed a host-wide helper lookup and timed out; it is retained in `evals/results/pstack-next/`. The next checker draft failed because it read truncated `actions.txt` rather than transcripts; that journal is `docs/RUN.pstack-next-checker-failed.json`. The task-context instruction now requires scoped symbol search and mapped callers. No external action, release, plugin install, or version change.
