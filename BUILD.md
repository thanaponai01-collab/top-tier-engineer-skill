# Build evidence

`python -m unittest discover tests -p test_challenge.py`: real CLI catches a source mutation, reports a survivor and rejects a harness failure without changing the source tree | proven (11 focused CLI checks; full suite 337 passed) | this slice

## Deferred

- Automatic mutation generation | one explicitly chosen mutation is enough for this mode | revisit when a requested challenge needs multiple mutation operators
