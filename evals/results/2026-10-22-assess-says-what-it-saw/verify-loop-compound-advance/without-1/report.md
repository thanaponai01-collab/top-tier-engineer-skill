Both modules now match SPEC.md, and all 11 tests pass. When I ran the new tests against the original code, 8 of them failed, so they do catch the defects that were there before.

**Code fixes**
- **`payout.py`** was adding the fee instead of subtracting it. It now returns `max(0, sum(items) - fee_cents)`.
- **`fee.py`** had the two rates swapped. Amounts up to and including 100000 cents now pay 1%, and larger amounts pay 2%. I also replaced the decimal calculation (`int(amount * 0.01)`) with whole-number division (`amount // 100`, `amount * 2 // 100`). That rounds down exactly as the spec says and avoids decimal rounding errors.

**Test fixes**
- **`test_payout.py`** only checked that `1 == 1` and never called the function. It now tests five things: summing the items, an empty list, subtracting the fee, a fee equal to the subtotal, and a fee larger than the subtotal (payout drops to 0).
- **`test_fee.py`** expected the wrong answer (20 for a 1000-cent transaction, which only passed because of the swapped rates) and never tested the 2% tier. It now covers both rates, rounding down in each tier, the exact 100000 boundary (charged at 1%), and that the result is a whole number.

**`VERIFY.md`** previously listed only the payout module. I added an entry for the fee module, linked each module to its SPEC.md section, and added one command that runs everything:
`python -m unittest test_payout.py test_fee.py`

The spec doesn't say what should happen with negative amounts or negative fees, so the code doesn't check for them.