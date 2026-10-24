# Trigger eval: 2026-10-25-0446

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/d-short-weak-tests.txt.

> Use when someone needs to know a change really works or a task is really done: before a commit, doubting a fix or an agent's "done", wanting proof not opinion, verifying or reviewing a diff or PR, or doubting that passing tests would notice a broken result. Also makes or maintains a project /verify skill. Proves a check fails on broken code, then passes. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 13/14 | 0/14 | 27/28 |
| test | 0/0 | 0/0 | 0/0 |
| all | 13/14 | 0/14 | 27/28 |

Invalid tries (leak or error): 0. Cost $3.34.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-agent-said-done | train | fire | 2/2 |  |
| f-create-verify-skill | train | fire | 2/2 |  |
| f-make-sure | train | fire | 2/2 |  |
| f-review-proof | train | fire | 2/2 |  |
| f-tests-catch | train | fire | 2/2 |  |
| f-trust-green ✗ | train | fire | 1/2 |  |
| f-verify-change | train | fire | 2/2 |  |
| n-commit | train | quiet | 0/2 |  |
| n-debug-zero | train | quiet | 0/2 |  |
| n-docstring | train | quiet | 0/2 |  |
| n-explain | train | quiet | 0/2 |  |
| n-git-email | train | quiet | 0/2 |  |
| n-rename | train | quiet | 0/2 |  |
| n-run-tests | train | quiet | 0/2 |  |
