# Build evidence

`python -m unittest discover tests -p test_challenge.py`: real CLI catches a source mutation, reports a survivor and rejects a harness failure without changing the source tree | proven (11 focused CLI checks; full suite 337 passed) | 179a62e

`python -m unittest discover tests -p test_challenge.py`: sequential feature challenges retain both receipts and finish strict green; live change evaluation detects a shared-caller regression and completes verification | proven (12 challenge checks, 5 grader checks and full suite 343 passed; live case passed) | 7b89281

`python -m unittest discover tests -p test_ci.py`: fresh CI proof ignores local state, rejects a survivor and bad product, and records checkout identity | proven (6 CLI checks; full suite 349 passed; live mode passed) | this slice

Pinned GitHub Actions example executes fresh proof and uploads commit-bound artifacts | planned | uncommitted

## Deferred

- Automatic mutation generation | one explicitly chosen mutation is enough for this mode | revisit when a requested challenge needs multiple mutation operators
