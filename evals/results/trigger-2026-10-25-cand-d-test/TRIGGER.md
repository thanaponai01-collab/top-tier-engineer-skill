# Trigger eval: 2026-10-25-0450

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: evals/trigger/candidates/d-short-weak-tests.txt.

> Use when someone needs to know a change really works or a task is really done: before a commit, doubting a fix or an agent's "done", wanting proof not opinion, verifying or reviewing a diff or PR, or doubting that passing tests would notice a broken result. Also makes or maintains a project /verify skill. Proves a check fails on broken code, then passes. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 0/0 | 0/0 | 0/0 |
| test | 8/12 | 0/12 | 20/24 |
| all | 8/12 | 0/12 | 20/24 |

Invalid tries (leak or error): 0. Cost $2.70.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail | test | fire | 2/2 |  |
| f-confirm-claude-fixed | test | fire | 2/2 |  |
| f-did-it-work ✗ | test | fire | 1/2 |  |
| f-double-check-merge ✗ | test | fire | 0/2 |  |
| f-prove-negative ✗ | test | fire | 1/2 |  |
| f-refund-claim | test | fire | 2/2 |  |
| n-feature | test | quiet | 0/2 |  |
| n-python-version | test | quiet | 0/2 |  |
| n-style | test | quiet | 0/2 |  |
| n-summarize-log | test | quiet | 0/2 |  |
| n-verify-install | test | quiet | 0/2 |  |
| n-write-test | test | quiet | 0/2 |  |
