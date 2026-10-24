# Trigger eval: 2026-10-25-0411

Model `claude-sonnet-5-5`, 1 tries a prompt, --max-turns 6. Description: plugin SKILL.md.

> Prove a change or claim with a check seen failing, then passing, and keep the evidence. Use when a user, skill or agent asks to verify a change, prove a task is done, check a claim against the real app, review a PR or agent's change by proof, or create or maintain a project verify skill; VERIFY.md recipes. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 3/7 | 0/7 | 10/14 |
| test | 1/6 | 0/6 | 7/12 |
| all | 4/13 | 0/13 | 17/26 |

Invalid tries (leak or error): 0. Cost $1.17.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail ✗ | test | fire | 0/1 |  |
| f-confirm-claude-fixed ✗ | test | fire | 0/1 |  |
| f-did-it-work ✗ | test | fire | 0/1 |  |
| f-double-check-merge ✗ | test | fire | 0/1 |  |
| f-prove-negative | test | fire | 1/1 |  |
| f-refund-claim ✗ | test | fire | 0/1 |  |
| f-agent-said-done ✗ | train | fire | 0/1 |  |
| f-create-verify-skill | train | fire | 1/1 |  |
| f-make-sure ✗ | train | fire | 0/1 |  |
| f-review-proof | train | fire | 1/1 |  |
| f-tests-catch ✗ | train | fire | 0/1 |  |
| f-trust-green ✗ | train | fire | 0/1 |  |
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
