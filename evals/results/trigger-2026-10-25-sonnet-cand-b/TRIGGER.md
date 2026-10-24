# Trigger eval: 2026-10-25-0411

Model `claude-sonnet-5-5`, 1 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/b-weak-tests.txt.

> Use whenever someone wants to know that a change really works or a task is really done, not just hear that it is: making sure a change works before committing, doubting a fix or another agent's "done", asking for proof instead of an opinion, asking to verify or review a diff, commit, branch or PR, or doubting that passing tests check anything (would they notice a broken result, does green mean working). Also for creating or maintaining a project's /verify skill or VERIFY.md. Its helper shows a check failing on a broken product and passing on the fixed one, finds tests that cannot fail, and keeps that record, which checking by hand does not. Not for just running tests, building features or explaining code.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 7/7 | 0/7 | 14/14 |
| test | 4/6 | 0/6 | 10/12 |
| all | 11/13 | 0/13 | 24/26 |

Invalid tries (leak or error): 0. Cost $1.36.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail | test | fire | 1/1 |  |
| f-confirm-claude-fixed | test | fire | 1/1 |  |
| f-did-it-work | test | fire | 1/1 |  |
| f-double-check-merge ✗ | test | fire | 0/1 |  |
| f-prove-negative | test | fire | 1/1 |  |
| f-refund-claim ✗ | test | fire | 0/1 |  |
| f-agent-said-done | train | fire | 1/1 |  |
| f-create-verify-skill | train | fire | 1/1 |  |
| f-make-sure | train | fire | 1/1 |  |
| f-review-proof | train | fire | 1/1 |  |
| f-tests-catch | train | fire | 1/1 |  |
| f-trust-green | train | fire | 1/1 |  |
| f-verify-change | train | fire | 1/1 |  |
| n-feature | test | quiet | 0/1 |  |
| n-python-version | test | quiet | 0/1 |  |
| n-style | test | quiet | 0/1 |  |
| n-summarize-log | test | quiet | 0/1 |  |
| n-verify-install | test | quiet | 0/1 |  |
| n-write-test | test | quiet | 0/1 |  |
| n-commit | train | quiet | 0/1 |  |
| n-debug-zero | train | quiet | 0/1 |  |
| n-docstring | train | quiet | 0/1 |  |
| n-explain | train | quiet | 0/1 |  |
| n-git-email | train | quiet | 0/1 |  |
| n-rename | train | quiet | 0/1 |  |
| n-run-tests | train | quiet | 0/1 |  |
