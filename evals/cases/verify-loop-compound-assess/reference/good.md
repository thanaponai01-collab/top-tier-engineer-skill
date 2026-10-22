# Verification Health Audit

VERDICT: red. Do not ship.

## Summary of Findings

1. **Hollow Tax Check**:
   `test_tax.py` is hollow and provides zero coverage for `tax.py`. It never calls `calculate_tax`, only asserting `assertEqual(default_rate, 0.05)` on its own local variable. The tax exemption logic in `tax.py` is untested and buggy.

2. **Loosened Invoice Check**:
   In `test_invoice.py`, CI deflake commits loosened exact equality assertions to `assertAlmostEqual(..., delta=2)`. This weaker tolerance hides an underlying regression.

3. **Rounding Regression in Invoice**:
   `invoice.py` was altered to calculate discounts per line before summing, truncating cents on each line instead of rounding the total half-up. On two 105-cent lines at 10%, it calculates 188 cents instead of 189 cents. The loosened `delta=2` test passes only because the error is within two cents.

4. **Coupon Cap Mutation Survivor**:
   The `Coupons` recipe in `VERIFY.md` has no `path:` declared. Automated challenge surveying `coupons.py` revealed a mutation survivor where altering the coupon cap from 5000 still passed because `test_coupons.py` only tests small amounts under the limit.

5. **Unmapped Rebate Module**:
   `rebate.py` exists in the repository but is completely unmapped in `VERIFY.md` without any verification recipe or blind spot note.

6. **Shipping Decoy Verification**:
   The `Shipping` contract is genuine and healthy: `shipping.py` and `test_shipping.py` caught 100% of injected mutations with no survivors. Shipping check is fine.

## Recommendation
This branch is blocked. Do not ship until tax tests are repaired, invoice rounding is fixed, coupon cap tests are added, and rebate.py is mapped.
