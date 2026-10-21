# Refund fix

The earlier session changed refund.py to `credit + amount` and added a test. I ran
`python -m unittest test_refund.py`: 2 tests, OK.

The code matches SPEC.md and the tests pass, so the fix is proven. Safe to merge.
