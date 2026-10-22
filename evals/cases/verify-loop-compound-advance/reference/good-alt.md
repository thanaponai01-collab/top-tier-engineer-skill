# Verification Report: Settlement Modules

Status: The initial codebase should not go out; repair first before advancing.

### Verification Deficiencies Addressed

- **Hollow Test in Payout**:
  `test_payout.py` does not call `calculate_payout` in `payout.py`. The original check was a self-fulfilling tautology that could never fail.

- **Payout Fee Defect**:
  `payout.py` implemented `+ fee` instead of `- fee_cents`. The spec says fee is deducted from the batch total, so the implementation should subtract fee.

- **Unmapped Code**:
  `fee.py` was not mapped in `VERIFY.md` and had no contract tracking its behavior.

- **Tier Rate Inversion**:
  `fee.py` applied the wrong rate by swapping the threshold: 0.01 was assigned for values over 100000 cents rather than standard amounts.

- **Baseline Completion**:
  Both modules were mapped, fail-proofs demonstrated with challenge receipts, and state frozen.
