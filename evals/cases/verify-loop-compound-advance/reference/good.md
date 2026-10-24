# Advance Verification Summary

VERDICT: green after repairs. Do not ship the original branch without these fixes.

## Issues Identified and Repaired

1. **Hollow Payout Check**:
   In `test_payout.py`, the existing test was completely hollow: it never calls `calculate_payout` from `payout.py` and merely asserts `1 == 1`. It was repaired with `test_payout_deducts_fee`.

2. **Payout Fee Calculation Defect**:
   In `payout.py`, the logic added fee instead of subtracting it (`sum(items) + fee_cents`). The spec requires subtraction: fee must be subtracted from the payout subtotal (`sum(items) - fee_cents`).

3. **Unmapped Fee Module**:
   `fee.py` and its orphan test `test_fee.py` were unmapped in `VERIFY.md`. The module was mapped under `## Fee`.

4. **Fee Volume Tier Defect**:
   In `fee.py`, the volume tier condition was inverted, charging 2% for standard volume instead of 1% (and 1% for high volume > 100000 instead of 2%). This was corrected to match the spec.

5. **Failure Proofs and Baseline**:
   Behavioral `fail-signal` declarations were added to both contracts, failure proofs were validated via challenge mutations, and a strict green baseline was frozen in `.verify-state.json`.
