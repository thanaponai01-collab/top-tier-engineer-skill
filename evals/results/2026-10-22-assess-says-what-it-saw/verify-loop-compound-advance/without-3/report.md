Both modules now meet SPEC.md, and the full suite passes: 12 of 12 tests, run with the commands listed in VERIFY.md. Before the fixes, the new tests failed 9 of 12 against the original code, so they do catch the defects.

**Code fixes**
- **`fee.py`:** the two fee tiers were swapped, so standard amounts were charged 2% and high-volume amounts 1%. It now charges 1% up to and including 100000 cents and 2% above that. It also uses whole-number math instead of decimals, so rounding down stays exact even for very large amounts.
- **`payout.py`:** the fee was being added to the subtotal instead of subtracted. The net payout is now the subtotal minus the fee, and it never goes below 0.

**Test fixes**
- **`test_payout.py`:** the old test only checked `1 == 1` and never called the payout function. It now has 5 tests covering:
  - the subtotal being the sum of the items
  - an empty item list
  - the fee being subtracted
  - a fee equal to the subtotal giving 0
  - a fee larger than the subtotal giving 0
- **`test_fee.py`:** the old test asserted the wrong value (20 instead of 10 for 1000 cents), so it passed only because of the bug. It never tested the high-volume tier. It now has 7 tests covering:
  - the 1% fee
  - rounding down in both tiers
  - the limit itself (100000 cents is still standard, 100001 is high-volume)
  - the 2% fee
  - zero
  - a very large amount, to check that rounding stays exact

**VERIFY.md** only listed the payout module, so I added an entry for the fee module with `python -m unittest test_fee.py`.