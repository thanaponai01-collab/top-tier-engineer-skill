## Shipping
- test: `python -m unittest test_shipping.py`
- fail-signal: shipping fee mismatch
- oracle: SPEC.md, change.diff
- fail-proof: moved shipping minimum back to 100 in scratch; shipping at 50 rejected

## Discount
- test: `python -m unittest test_discount.py`
- fail-signal: discount mismatch
- fail-proof: moved discount minimum to 50 in scratch; discount at 50 rejected
