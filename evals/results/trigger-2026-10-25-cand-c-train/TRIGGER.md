# Trigger eval: 2026-10-25-0443

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/c-short.txt.

> Use when someone needs to know a change really works or a task is really done: before a commit, when doubting a fix or an agent's "done", when asking for proof not opinion, to verify or review a diff or PR, or when passing tests may not check anything. Also makes or maintains a project /verify skill. Records a check failing on broken code, then passing. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 11/14 | 0/14 | 25/28 |
| test | 0/0 | 0/0 | 0/0 |
| all | 11/14 | 0/14 | 25/28 |

Invalid tries (leak or error): 0. Cost $3.28.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-agent-said-done | train | fire | 2/2 |  |
| f-create-verify-skill | train | fire | 2/2 |  |
| f-make-sure | train | fire | 2/2 |  |
| f-review-proof | train | fire | 2/2 |  |
| f-tests-catch ✗ | train | fire | 0/2 |  |
| f-trust-green ✗ | train | fire | 1/2 |  |
| f-verify-change | train | fire | 2/2 |  |
| n-commit | train | quiet | 0/2 |  |
| n-debug-zero | train | quiet | 0/2 |  |
| n-docstring | train | quiet | 0/2 |  |
| n-explain | train | quiet | 0/2 |  |
| n-git-email | train | quiet | 0/2 |  |
| n-rename | train | quiet | 0/2 |  |
| n-run-tests | train | quiet | 0/2 |  |
