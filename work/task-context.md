# Task context across skills

Owner intent (2026-10-13): fresh agents recover context relevant to their assigned task and trace
records, code history and verification themselves. Shared procedure:
`skills/project-context/references/memory.md#task-context`. The skill uses that procedure;
context-handoff links it for building skills, and foundation writes a conditional installed-path
pointer into project startup instructions. This repository's CLAUDE.md already includes the pointer.
Other projects need their startup pointer refreshed; installing a skill alone does not edit them.

The index remains a read-only source of context pointers, not a source-code or Git index.
Git history and actual callers are inspected directly when needed. Available context is reused;
retrieval returns to the current task without invoking an entire resumption or history workflow.

New case: `evals/cases/project-context-task-trail/` joins owner intent, relevant commits, unfinished
work and a safe current check against an older passing receipt. Baseline: 1/1 passed, so no
behavioral advantage is established. Evidence: `evals/results/context-task-trail-baseline/`.
With-skill trials and regression results: `evals/results/context-task-retrieval-with/` (5/5 passed).
After splitting the task procedure into references/task-context.md, both context cases passed
again in `evals/results/context-task-retrieval-final/`. The final task-trail transcript shows the
reference being read, relevant history inspected and the safe check rerun. Foundation's transcript
shows the installed task-context pointer written to startup instructions. All 484 tests passed;
catalog and initial handoff checks passed. The baseline also passed, so no improvement claim is made.
Storage detail now lives in references/storage.md; scoped checks and 20 context-instruction tests
pass. Later broad handoff checking found an unrelated missing packages/auth/VERIFY.md link after
concurrent work appeared; that work is preserved. Replay: evals/results/context-task-storage-split/.
Validation is summarized in evals/RESULTS.md; helper tests and live behavior are separate claims.

Next: test a fresh working skill in a larger project with the startup pointer, missing mappings
and a shared caller outside the named area; require action evidence of relevant loading and no
unrelated full-repository sweep. Existing fixtures do not prove all skills follow the procedure.
