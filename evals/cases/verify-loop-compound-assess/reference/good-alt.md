# Audit Report

Status: Hold — this release should not go out.

### Key Verification Deficiencies

- **Tax Check is Hollow**:
  The suite passes, but `test_tax.py` does not call `calculate_tax` in `tax.py`. It is a tautology checking its own constants, so code changes in `tax.py` have zero real validation.

- **Invoice Assertions Weakened**:
  Git history shows `test_invoice.py` was weakened by ci-bot using a tolerance window. An exact assertion was replaced with `delta of 2`.

- **Invoice Floor Regression**:
  The weakened tolerance disguises a bug in `invoice.py`: it floors each line during discount calculations rather than applying half-up rounding to the aggregated subtotal.

- **Unmapped Code**:
  `rebate.py` is not mapped in `VERIFY.md` and has no test coverage tracked.

- **Coupons Challenge Gaps**:
  Because `Coupons` lacks a recipe path, challenge inspected `coupons.py`. An untested cap boundary mutation survived (the check still passed with off-by-one errors on `cap=5000`).

- **Shipping Status**:
  Shipping passed challenge completely without issues: `test_shipping.py` is genuine and shipping is solid.

The codebase is not ready for deployment.
