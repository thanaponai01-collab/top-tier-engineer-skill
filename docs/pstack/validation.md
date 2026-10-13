# PStack adoption validation

Status: [handoff](../../work/pstack-handoff.md). Proposed work: [plan](adoption-plan.md).

## Available evidence and corrections

Source comparison establishes that mechanisms appear in inspected instructions, not execution
reliability or comparative savings. Local results remain owned by [RESULTS.md](../../evals/RESULTS.md),
[PROJECT_MEMORY.md](../../evals/PROJECT_MEMORY.md) and their artifacts. Existing passing counts
must not be presented as new adoption proof.

Historical trials leaked installed-plugin/user instructions into baseline sessions. RESULTS.md
describes subsequent isolation changes and preserves contaminated runs. Inspect actual runner,
environment and action logs before interpreting an older table. Selected isolated cases show
benefit; others show no difference. A review trial switched the user's checkout against instructions.

The 2026-10-13 recall replay's counter reports no skill opening, but its action log records a Read
of the staged recall SKILL.md. The earlier conversational conclusion that the skill was not read
is corrected. Loading occurred; the mismatch is a reporting defect. Reading alone does not prove
full procedure compliance or improvement over baseline. See [recall work](../../work/recall-improvement.md)
and [actions](../../evals/results/2026-10-13-1147/recall-stale-proof/with-1/actions.txt).

## Proposed acceptance trials

| Trial | Intended discrimination | Independent observation |
|---|---|---|
| Skill loading | Direct Read, Skill call and absent read differ | Compare transcript paths to actual staged skill files. |
| Fresh reader | Recover changed intent, unfinished work and Next | Compare capsule/actions to externally held expectations. |
| Repeat upkeep | Second unchanged pass preserves records | Compare bytes and inspect distinct second-pass actions. |
| Recovery | Preserve edits and reconcile uncertain action | Check resumed artifact and harmless action count/marker. |
| Wrong build | Responsive stale instance is rejected | Serve distinguishable builds on the expected port. |
| Persistence | Success toast alone cannot pass | Read stored result through a second entry path. |
| Failed cleanup | Proof survives, owned residue goes | Inspect artifacts, owned process and unrelated control instance. |
| Benchmark no-op | Fast absent/incorrect work fails | Check work/error counts and concrete output. |
| Design uncertainty | Explore costly forks, skip routine edits | Judge contracts/outcome blind to variant and model. |
| Indirect regression | Reach an unchanged consumer/format | Replay supplied bad/correct behavior through that consumer. |

These are designs, not completed cases. Reuse existing discrimination where available. Begin with
one bounded pair/pilot, then repeat selected cases. Targets and total budgets remain unassigned;
there is no agreed universal pass-rate or cost-reduction threshold for this proposal.

## Experiment controls

Compare the same organic task, fixture, model and budget when measuring a skill change. Keep
expectations outside candidate access. Inspect installed plugins, settings, hooks and environment
isolation. Sanitize labels revealing experimental arms. A judge may see the rubric but not
variant/model identity. Read artifacts/transcripts; never credit self-reported procedure alone.
Judge calibration is harness evidence, not live outcome evidence.

Report dimensions separately:
- Outcome: independently correct behavior and allowed changed files.
- Routing: actual skill reads, including direct file access.
- Procedure: observed required actions, omissions and ambiguity.
- Proof: meaningful rejection, current pass, artifact and material environment.
- Cost: available spend/tokens, elapsed time, dispatch count and context loaded.

Retain failed, blocked, budget-limited and inconclusive runs. Usage-limit errors before work are
runner failures. One pass is a smoke trial. Repeated small-fixture results support only the
tested fixture/model/budget scope. Comparative savings require comparable measured runs.

## Future change checks

Read relevant skill/eval instructions before a future slice. Add helper regressions where
enforcement changes. Consult python evals/run.py --help before constructing live commands.
Repository policy requires actual behavioral replay after a skill change; before committing run
the required suite. Regenerate/check catalogs when names/descriptions change. These are future
steps, not commands executed for this handoff.

Mark a slice verified only when its acceptance checks ran on final relevant inputs, retained
output/transcripts resolve, coverage gaps are named and its status links evidence. Helper green,
another model's approval or a generated recipe alone is insufficient. Resume from current
BUILD.md/RUN.json and this handoff. Recheck source freshness and preserve concurrent edits.
