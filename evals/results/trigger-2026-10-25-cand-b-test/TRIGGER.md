# Trigger eval: 2026-10-25-0411

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/b-weak-tests.txt.

> Use whenever someone wants to know that a change really works or a task is really done, not just hear that it is: making sure a change works before committing, doubting a fix or another agent's "done", asking for proof instead of an opinion, asking to verify or review a diff, commit, branch or PR, or doubting that passing tests check anything (would they notice a broken result, does green mean working). Also for creating or maintaining a project's /verify skill or VERIFY.md. Its helper shows a check failing on a broken product and passing on the fixed one, finds tests that cannot fail, and keeps that record, which checking by hand does not. Not for just running tests, building features or explaining code.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 0/0 | 0/0 | 0/0 |
| test | 10/12 | 0/12 | 22/24 |
| all | 10/12 | 0/12 | 22/24 |

Invalid tries (leak or error): 0. Cost $2.85.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail | test | fire | 2/2 |  |
| f-confirm-claude-fixed | test | fire | 2/2 |  |
| f-did-it-work | test | fire | 2/2 |  |
| f-double-check-merge ✗ | test | fire | 0/2 |  |
| f-prove-negative | test | fire | 2/2 |  |
| f-refund-claim | test | fire | 2/2 |  |
| n-feature | test | quiet | 0/2 |  |
| n-python-version | test | quiet | 0/2 |  |
| n-style | test | quiet | 0/2 |  |
| n-summarize-log | test | quiet | 0/2 |  |
| n-verify-install | test | quiet | 0/2 |  |
| n-write-test | test | quiet | 0/2 |  |
