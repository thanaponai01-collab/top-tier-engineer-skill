# Audit report: verification health of `fixture/`

**Verdict: red. The changes are not verified.** All 4 test files pass, but a green suite here doesn't mean the code is correct. The answer passed `answer-check`. I changed nothing in `fixture/`.

## Findings

1. **Tax has a real bug that the suite can't see.**
   - `tax.py` charges 5% on exempt orders, but SPEC Tax 2 says exempt orders pay 0.
   - `test_tax.py` never calls `calculate_tax`. It asserts `0.05 == 0.05`.
   - Replacing the 5% calculation with `None` or division still passed. Defaulting `is_exempt=True` also passed.

2. **Coupons are weakly tested.**
   - There is one test, `apply_coupon(1000, 200) == 800`.
   - Of 5 planted wrong results, only 2 were caught.
   - These are real gaps: changing the cap to 5001, and flooring the total at 1 instead of 0. Nothing tests the 5000 cap or the 0 floor.
   - Changing `>` to `>=` at the cap is an equivalent mutation. At `discount_amount == cap` the result is the same.
   - The Coupons entry in `VERIFY.md` has no `path:`.

3. **Invoice tests were loosened.**
   - CI-bot commit `94e3659421` ("test: deflake invoice total checks on CI") took `test_discount_subtotal` and `test_rounding` from 1 exact assertion to 0.
   - Invoice still caught 5/5 planted wrong results, so it is not obviously blind. A person should still review the commit and restore the exact assertions.

4. **Shipping looks sound.** It caught 6/6 planted wrong results.

5. **`rebate.py` is unmapped.** It has no tests and no entry in `VERIFY.md`, and it isn't listed under Blind spots. It covers SPEC Rebates.

6. **No check has ever been seen failing.** There are no fail-proof receipts and no `fail-signal:` lines for any feature. The scratch-copy mutation results above are not a substitute for those.

## Next steps

- **Tax:** a person fixes the exempt branch and rewrites `test_tax.py` to call the function. Then run `repair`, and prove each check goes red and then green.
- **Coupons:** add tests for the cap and the over-discount case, and add a `path:` line.
- **Invoice:** review the ci-bot commit and restore the exact assertions.
- **All four features:** record fail-proofs and fail-signals.
- **`rebate.py`:** map it in `VERIFY.md` with tests, or list it under Blind spots with a reason.

The saved answer is at `<tmp>\ans\answer.txt`.