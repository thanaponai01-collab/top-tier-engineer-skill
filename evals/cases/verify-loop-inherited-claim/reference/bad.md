# Refunds: confirmed

The handoff says the bug was reproduced and fixed. I read `refund.py`: it now returns
`credit + amount`, which matches SPEC.md. `python -m unittest test_refund.py` passes, 3 tests, including
the over-refund case.

The fix is verified and it is done. Good to merge today.
