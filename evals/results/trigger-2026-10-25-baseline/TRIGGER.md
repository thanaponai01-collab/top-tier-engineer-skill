# Trigger eval: 2026-10-25-0403

Model `claude-opus-5-5`, 2 tries a prompt, --max-turns 6. Description: plugin SKILL.md.

> Prove a change or claim with a check seen failing, then passing, and keep the evidence. Use when a user, skill or agent asks to verify a change, prove a task is done, check a claim against the real app, review a PR or agent's change by proof, or create or maintain a project verify skill; VERIFY.md recipes. Not for just running tests.

| split | fired when wanted | fired when not | right |
|---|---|---|---|
| train | 6/14 | 0/14 | 20/28 |
| test | 3/12 | 0/12 | 15/24 |
| all | 9/26 | 0/26 | 35/52 |

Invalid tries (leak or error): 0. Cost $5.68.

| case | split | want | fired | other skills |
|---|---|---|---|---|
| f-check-would-fail ✗ | test | fire | 1/2 |  |
| f-confirm-claude-fixed ✗ | test | fire | 0/2 |  |
| f-did-it-work ✗ | test | fire | 0/2 |  |
| f-double-check-merge ✗ | test | fire | 0/2 |  |
| f-prove-negative | test | fire | 2/2 |  |
| f-refund-claim ✗ | test | fire | 0/2 |  |
| f-agent-said-done ✗ | train | fire | 0/2 |  |
| f-create-verify-skill | train | fire | 2/2 |  |
| f-make-sure ✗ | train | fire | 0/2 |  |
| f-review-proof | train | fire | 2/2 |  |
| f-tests-catch ✗ | train | fire | 0/2 |  |
| f-trust-green ✗ | train | fire | 0/2 |  |
| f-verify-change | train | fire | 2/2 |  |
| n-feature | test | quiet | 0/2 |  |
| n-python-version | test | quiet | 0/2 |  |
| n-style | test | quiet | 0/2 |  |
| n-summarize-log | test | quiet | 0/2 |  |
| n-verify-install | test | quiet | 0/2 |  |
| n-write-test | test | quiet | 0/2 |  |
| n-commit | train | quiet | 0/2 |  |
| n-debug-zero | train | quiet | 0/2 |  |
| n-docstring | train | quiet | 0/2 |  |
| n-explain | train | quiet | 0/2 |  |
| n-git-email | train | quiet | 0/2 |  |
| n-rename | train | quiet | 0/2 |  |
| n-run-tests | train | quiet | 0/2 |  |
