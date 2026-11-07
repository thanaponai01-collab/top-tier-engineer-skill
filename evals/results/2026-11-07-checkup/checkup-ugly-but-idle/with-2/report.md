Overall the shop is structured reasonably well for its size. Only two problems are actually costing you time, so I can't honestly give you three things to fix: the third thing the checkup flagged has never cost a commit.

**What was measured:** 13 tracked files (12 of them code) and all 13 commits. A parser read 100% of the 204 lines of code. I changed nothing. I deleted the checkup's scratch folder `.checkup/` afterwards, so the working tree is clean.

| Property | Rating |
|---|---|
| Easy to find things | not checked (there's no `FEATURES.md` mapping each feature to its code) |
| One change in one place | **poor** |
| Dependencies point one way | good (no cycles; layer rules weren't checked because there's no `layers.txt`) |
| Deep modules, narrow doors | good |
| One way per job | **in places** |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked (that needs the tests run against broken code; verify-loop does that) |

## Fix first

1. **The discount rules are written out twice, in `shop/cart.py` and `shop/receipt.py`.** The member rate, the bulk threshold, the bulk rate and the rounding are copied into both files, and neither file imports the other. This is the most expensive problem in the repo:
   - Five commits had to edit both files together.
   - In `82b04a5` the member rate was changed in the cart only, and `716a01b` had to fix the receipt.
   - `fa4e4f0` fixed rounding that differed between the two.
   - `6c240fd` fixed a wrong bulk rate in both.
   - `1a0f135` added a test only to catch the two copies drifting apart.

   The fix is to keep the rules in one place and have the receipt use the cart's calculation. The untangle skill does this.

2. **HTTP calls are made two different ways, each with its own retry loop.** `shop/payments.py` uses `http.client` and `shop/notify.py` uses `urllib`. The retry, timeout and backoff logic was added to each file separately (`774a33f`, `a16bb3b`), then fixed one file at a time: timeouts in `1e77a42`, leaked connections in `1fd7dcc`, backoff in `15edf68`. The two have already drifted: emails now back off exponentially, but payments still wait 1, 2, 3, 4 seconds. One shared HTTP helper with a single retry policy would fix this. The cleanup skill does this.

3. **No third fix is earned yet.** The checkup also flagged `sales_tax()` in `legacy/tax_tables.py`: 61 lines, complexity 25, nested 9 deep. But no commit has touched it since the first one, and only checkout calls it. I recorded it as not worth fixing now. It becomes the third fix as soon as next quarter includes a change to tax rates or regions; at that point split it into a table of rates per region and category (the arch-design skill does this).

If you want a third item regardless, my recommendation is a check of the tests rather than the code. The only guard on the discount drift is two assertions in `tests/test_totals.py`, and nobody has confirmed they would fail if the code were broken.