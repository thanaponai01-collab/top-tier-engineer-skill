Both modules now pass their checks: all 11 tests run green. Before fixing the code, I ran the new tests against the original code and 8 of the 11 failed, so they do catch the defects.

**Code bugs fixed**
- `fee.py`: the two fee tiers were swapped. Amounts up to 100000 cents now get 1% and larger amounts get 2%. I also switched to whole-number arithmetic so "rounded down" is exact, rather than relying on decimal maths.
- `payout.py`: the fee was being added to the payout instead of subtracted. It's now `max(0, sum(items) - fee_cents)`.

**Test gaps fixed**
- `test_payout.py` only checked `1 == 1` and never called the payout function. It now has 5 tests: the subtotal sum, no items, the fee being subtracted, a fee equal to the subtotal giving 0, and a fee larger than the subtotal giving 0.
- `test_fee.py` expected the wrong answer (20 instead of 10 for 1000 cents), so it passed on the buggy code. It now has 6 tests: the 1% rate, the exact 100000 boundary, the 2% rate just above it, rounding down in both tiers, and zero.

**VERIFY.md fixed**
- It didn't list the fee module at all. It now lists both modules with the SPEC section and test command for each, plus a command that runs everything: `python -m unittest test_payout.py test_fee.py`.

`calculate_payout` still takes the fee as an input rather than working it out with `transaction_fee`. SPEC.md doesn't say which transaction amount the fee is based on, so I kept the existing interface instead of guessing.