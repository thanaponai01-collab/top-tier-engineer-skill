# Verify this change

Use for verification of a task, working diff, commit or branch. Reuse the existing loop and
challenge runner; discovery and impact analysis belong to the agent.

## Establish the boundary

Read the requested outcome and project instructions. Fix the comparison point once: resolve
the user-supplied base/ref to a commit SHA. For uncommitted work without a supplied base, use
the current HEAD. Inspect the complete diff against that point, including staged and unstaged
changes, and list untracked files separately. Read added files and the former side of deletions
and renames. Preserve the user's existing edits.

For a clean tree, identify the requested commit or range before claiming which change was
verified. In a non-Git folder, use the supplied diff or prior snapshot. If neither exists,
verify the task's stated claims and report that change coverage cannot be established.

## Follow behavior, then map checks

Read each changed entry point and trace its callers, shared helpers, stored data and external
contracts far enough to identify affected behavior. A changed constant can affect callers in
unchanged files. Include nearby regressions that rely on the same seam; a filename list alone
does not establish coverage. Read the existing tests rather than trusting their names.

Make a compact table in the final report: changed behavior or adjacent claim, independent
expectation, check command, result or gap. Derive expectations from the task, spec or contract.
List unreachable or unavailable surfaces explicitly. Do not require a whole-project inventory.

Reuse VERIFY.md. Add missing claims and regression checks while preserving existing mapped
features and expectations. Finish the commands, failure signals and declared oracles before
collecting rejection evidence. Explain any check repairs. An authorized fix task includes fixing
introduced product regressions; a verification-only request reports those regressions.

## Challenge and finish

Run the relevant checks through the helper. A green check that ignores the product needs repair
before it is frozen. After an authorized product fix, challenge the highest-risk check with
one spec-backed mutation using [challenge mode](challenge.md). A survivor is a verification
gap; an inconclusive experiment is not proof. Preserve frozen expectations when repairing gaps.

Strict completion still needs rejection proof for every mapped feature. Caught challenges retain
separate receipts, so additional feature challenges preserve earlier proof. Changing commands,
tests, failure signals, oracles or the Run recipe invalidates old receipts globally: finalize
the recipe first, then refresh evidence as needed. Never delete unrelated feature rows to obtain
green. If the retained recipe cannot be verified here, report partial coverage and the blocker.

Freeze the finished checks, run `verify.py tests --strict` after test changes, then run the whole
recipe with `verify.py run --strict` and `verify.py status`. `--only` is diagnostic and does not
record completion. Write any retained artifacts before the final run so status covers final inputs.

Report the comparison point, affected claims and adjacent regressions, meaningful rejection
output, final status, changed check files and remaining gaps. Strict green covers the retained
recipe; the impact table explains why those checks cover this change. Neither proves discovery
of every feature. A review request does not authorize committing, pushing or deploying its target.
