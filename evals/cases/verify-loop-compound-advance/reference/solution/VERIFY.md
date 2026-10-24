# Settlement Verification

## Payout
- path: payout.py
- test: `python -m unittest test_payout.py`
- fail-signal: payout fee deduction mismatch
- fail-proof: changed - fee_cents to + fee_cents in calculate_payout; python -m unittest test_payout.py failed with AssertionError: payout fee deduction mismatch

## Fee
- path: fee.py
- test: `python -m unittest test_fee.py`
- fail-signal: fee calculation mismatch
- fail-proof: changed 0.01 to 0.05 in transaction_fee; python -m unittest test_fee.py failed with AssertionError: fee calculation mismatch

## Blind spots
- Cross-currency fx conversion is handled by payment gateway upstream.
