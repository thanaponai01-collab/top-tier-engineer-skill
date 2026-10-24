# Trigger eval: 2026-10-25-0409

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/b-weak-tests.txt.

> Use whenever someone wants to know that a change really works or a task is really done, not just hear that it is: making sure a change works before committing, doubting a fix or another agent's "done", asking for proof instead of an opinion, asking to verify or review a diff, commit, branch or PR, or doubting that passing tests check anything (would they notice a broken result, does green mean working). Also for creating or maintaining a project's /verify skill or VERIFY.md. Its helper shows a check failing on a broken product and passing on the fixed one, finds tests that cannot fail, and keeps that record, which checking by hand does not. Not for just running tests, building features or explaining code.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 14/14 | 0/14 | 28/28 |
| test | 0/0 | 0/0 | 0/0 |
| all | 14/14 | 0/14 | 28/28 |

Invalid tries (leak or error): 0. Cost $3.34.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-agent-said-done | train | fire | 2/2 |  |
| f-create-verify-skill | train | fire | 2/2 |  |
| f-make-sure | train | fire | 2/2 |  |
| f-review-proof | train | fire | 2/2 |  |
| f-tests-catch | train | fire | 2/2 |  |
| f-trust-green | train | fire | 2/2 |  |
| f-verify-change | train | fire | 2/2 |  |
| n-commit | train | quiet | 0/2 |  |
| n-debug-zero | train | quiet | 0/2 |  |
| n-docstring | train | quiet | 0/2 |  |
| n-explain | train | quiet | 0/2 |  |
| n-git-email | train | quiet | 0/2 |  |
| n-rename | train | quiet | 0/2 |  |
| n-run-tests | train | quiet | 0/2 |  |
