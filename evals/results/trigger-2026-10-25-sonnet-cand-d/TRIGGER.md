# Trigger eval: 2026-10-25-0450

Model `claude-sonnet-5-5`, 1 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/d-short-weak-tests.txt.

> Use when someone needs to know a change really works or a task is really done: before a commit, doubting a fix or an agent's "done", wanting proof not opinion, verifying or reviewing a diff or PR, or doubting that passing tests would notice a broken result. Also makes or maintains a project /verify skill. Proves a check fails on broken code, then passes. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 7/7 | 0/7 | 14/14 |
| test | 2/6 | 0/6 | 8/12 |
| all | 9/13 | 0/13 | 22/26 |

Invalid tries (leak or error): 0. Cost $1.26.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail | test | fire | 1/1 |  |
| f-confirm-claude-fixed ✗ | test | fire | 0/1 |  |
| f-did-it-work ✗ | test | fire | 0/1 |  |
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
