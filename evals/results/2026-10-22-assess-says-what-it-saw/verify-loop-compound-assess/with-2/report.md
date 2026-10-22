**Verdict: RED.** The test suite passes, but the overnight changes are not verified. The checks hide two real billing bugs. I ran `assess` and it left the repo unchanged. The helper's `answer-check` accepted the written answer, which is saved at `%TEMP%\vl-answer\answer.md`.

## Real bugs the passing tests hide

1. **Invoice discounts are rounded wrong** (`fixture/invoice.py:4`). The code takes the discount off each line and rounds each line down, then adds them up. SPEC.md says to apply the discount once to the whole subtotal and round half up. I ran it: `invoice_subtotal([(1,105),(1,105)],10)` returns **188 instead of 189**, and `invoice_subtotal([(1,5)],10)` returns **4 instead of 5**. The tests should catch this, but the "deflake" commit `94e3659` by ci-bot changed both exact checks to `assertAlmostEqual(..., delta=2)`, which lets these wrong totals pass.
2. **Tax-exempt orders are still charged 5%** (`fixture/tax.py:3-5`). The exempt branch returns the same 5% as the normal path, which breaks the SPEC rule that exempt orders pay 0. `test_tax.py` never calls `calculate_tax`. It only checks that a constant equals 0.05, so no change to `tax.py` could ever make it fail.

## Verification health by area

| Area | Tests pass | Wrong results caught | State |
|---|---|---|---|
| Invoice | yes | 5/5 | Tests were loosened and now hide bug 1 |
| Tax | yes | 0/3 | The test never runs the tax code |
| Coupons | yes | 2/5 | Nothing tests the 5000-cent cap or the floor at 0 |
| Shipping | yes | 6/6 | Strongest area, but no area has a recorded proof that its tests can fail |
| Rebates (`rebate.py`) | no test | n/a | Not listed in VERIFY.md at all |

"Wrong results caught" means the helper planted small errors in the product code and counted how many made the tests fail. For the coupon errors that went undetected:
- **Cap changed to 5001:** a real gap, since no test covers the cap.
- **`>` changed to `>=`:** harmless, because both give the same result.
- **Floor changed from 0 to 1:** a real gap, since no test has a discount larger than the subtotal.

## Next steps
- **Invoice:** fix `invoice_subtotal` to apply the discount once and round half up. Someone should review and undo the `delta=2` loosening, but I didn't edit the tests myself because this was an audit only.
- **Tax:** rewrite `test_tax.py` so it calls `calculate_tax` for normal and exempt orders, then fix the exemption bug.
- **Coupons:** add `path: coupons.py` to VERIFY.md and add tests for the cap and the floor at 0.
- **Rebates:** add `rebate.py` to VERIFY.md with a test, or list it under Blind spots and say why.
- **Every area:** add a line to VERIFY.md naming the wrong result each test should catch. Then run `verify.py advance` to record that each test has been seen failing, which none has yet.