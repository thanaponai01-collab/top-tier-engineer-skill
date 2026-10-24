The verdict is **red**: these changes are not verified. The suite is green, but that's because the tests were loosened or never call the code, and there are at least two real bugs underneath. I ran `verify-loop assess` on `fixture/`, which leaves the repo unchanged, checked the results against `SPEC.md`, and ran the actual functions directly. The audit report passed the skill's own `answer-check` and is saved at `<tmp>\vl-answer\answer.md`.

## Verification health

| Feature | Tests | Would the tests catch a deliberately broken version? | Status |
|---|---|---|---|
| Invoice | Pass | Yes, 5 of 5, but two assertions were loosened | **Hides a real bug** |
| Tax | Pass | No, 0 of 3: the test never calls `calculate_tax` | **Test is empty; real bug** |
| Coupons | Pass | 2 of 5 | Weak |
| Shipping | Pass | 6 of 6 | Healthy, but no recorded proof it can fail |
| Rebate | None | `rebate.py` isn't covered by any check | **Untested** |

No check has a recorded proof that it can fail, and none has a `fail-signal:` line saying what failure should look like.

## Bugs the green suite hides

1. **Invoice discount rounding (commit `bc08dd2`).** The code discounts and rounds down each line separately. The spec says to apply the discount once to the whole subtotal and round half up.
   - `invoice_subtotal([(1,105),(1,105)], 10)` returns **188**; the spec gives **189**.
   - `invoice_subtotal([(1,5)], 10)` returns **4**; the spec gives **5**.
   - Both tests pass only because commit `94e3659` (ci-bot, "deflake") changed exact checks to `assertAlmostEqual(..., delta=2)`. That wasn't fixing a flaky test; it hid a wrong answer.
2. **Tax exemption ignored.** `calculate_tax(1000, is_exempt=True)` returns **50**; the spec says 0. The only test just asserts `0.05 == 0.05`.

## Weak or missing coverage

- **Coupons:** No test reaches the 5000-cent cap, and none has a discount larger than the subtotal. Two of the three survivors are real gaps. The third (`>` changed to `>=` on the cap check) is harmless, because both give the same result when the discount equals the cap.
- **Rebate:** `rebate.py` has no test. Its simple rule (5% over 100000 cents) also doesn't match the spec's monthly, retroactive, threshold-based rule, which a product owner needs to settle.

## Recommended next steps

1. Someone should review and revert the `delta=2` loosening back to exact `assertEqual`. This will turn the suite red as it should, and then the billing author fixes `invoice.py`. I didn't make that change, since reverting another person's test edit needs a person's sign-off.
2. Rewrite `test_tax.py` to call `calculate_tax` with standard and exempt cases, then fix the exempt branch to return 0.
3. Add `path: coupons.py` to the Coupons section in `VERIFY.md`, plus tests at and above the cap and for a discount larger than the subtotal.
4. Add `rebate.py` to `VERIFY.md` with a test, or list it as a known blind spot.
5. Run `verify.py advance fixture/` to add the fail-signals and recorded fail proofs.