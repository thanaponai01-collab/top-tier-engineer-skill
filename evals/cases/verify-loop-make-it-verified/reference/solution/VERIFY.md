## Refunds
- test: `python -m unittest test_refund.py`
- fail-proof: replaced apply_refund with a function that raises, the old suite stayed green; pointed the test at data/refund_cases.json and it went red on the sign bug, then green after the fix
- oracle: SPEC.md, data/refund_cases.json
- fail-signal: AssertionError:
