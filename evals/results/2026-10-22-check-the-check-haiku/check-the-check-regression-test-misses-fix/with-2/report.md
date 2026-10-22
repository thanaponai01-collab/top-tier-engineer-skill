**No, the regression test does not prove the bug is fixed.** It passes on `main`, where the bug is still present, and it still passes when I put the bug back.

The bug was in `invoice_total`, which used `paid >= due`. The PR changes `invoice_total` to call `late_fee`, which uses `paid > due`. But `test_due_date_is_not_late` only calls `late_fee` directly. `late_fee` was already correct on `main`, so the test doesn't exercise the code that was broken.

What I ran (the repo is unchanged; the helper works in a scratch copy):

- **Helper, `--base main`, check `python -m unittest test_billing`** (there's no CI config in the fixture, so I used the plain unittest command): 5 tests pass. The new test `test_due_date_is_not_late` **passes on `main`**, so it "cannot catch what this change fixed." Verdict: `weak`.
- **Scratch copy with the old `invoice_total` restored** (`fee = ... if paid >= due`): all 5 tests still pass. `invoice_total(200.0, 2026-03-31, 2026-03-31)` returns **210.0**, which is the exact bug from #12.

Gaps the helper found:

1. **Invoice-level bug is untested (the real gap).** No test checks `invoice_total` on the due date. Closing it: `invoice_total(200.0, DUE, DUE)` should equal `200.0`. This is the test that would have failed before the fix.
2. **Fee rounding is untested for non-round amounts.** Changing `round(amount * LATE_FEE_RATE, 2)` to 3 decimals survives because every test uses `200.0` (fee exactly 10.0). Closing it: `late_fee(DUE, date(2026, 4, 2), 10.01)` should equal `0.5`, since fees are to the cent; the 3-decimal mutant returns `0.501`.
3. The second survivor (rounding in `invoice_total`'s final `round(..., 2)`) changes nothing observable for cent-precision amounts, so it's not a gap.

What held: the early-payment and late-payment rules are covered. Breaking the late fee's threshold is caught by the existing tests.

I'd request changes on the PR for gap 1 before approving. Gap 2 is worth adding at the same time. I haven't added either test; say the word if you want me to write them and verify them with the verify-loop skill.