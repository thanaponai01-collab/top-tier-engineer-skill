I ran the checkup on all 13 tracked files (12 of them code) and the full 13-commit history. Two problems clearly cost you every time you change the code. There isn't a third that has cost you anything yet, so my third pick is a weaker one. I changed nothing, and I deleted the temporary `.checkup/` folder, so the working tree is clean.

## How well it's structured

| Property | Verdict |
|---|---|
| Easy to find things | not checked: there's no `FEATURES.md` mapping each feature to its code |
| One change in one place | **poor** |
| Dependencies point one way | good (no cycles; layer rules not checked, since there's no `layers.txt`) |
| Deep modules, narrow doors | in places |
| One way per job | **poor** |
| Logic apart from I/O | good (network code stays in `payments.py` and `notify.py`) |
| No dead code | good |
| Tests that can fail | not checked: that needs the tests run against deliberately broken code |

Overall the layout is small and clean. The problems are copied code, not tangled code.

## What to fix first

**1. The discount rules exist twice, in `shop/cart.py` and `shop/receipt.py`.** Both files define the member discount, the bulk threshold, the bulk percentage and the rounding, and neither imports the other. The two files changed together in 5 of 13 commits, and the copies have already drifted apart:
- `82b04a5` changed the member discount only in the cart.
- `716a01b` then fixed the receipt not matching the cart.
- `fa4e4f0` fixed the two files rounding differently.

Every other pricing change (`ba474a1`, `27069c6`, `6c240fd`) also had to be made twice. The test in `tests/test_totals.py` catches a mismatch after it happens; it doesn't prevent one. The fix is one pricing function that both files call, and the `untangle` skill does this.

**2. Two hand-written retry loops for HTTP.** `payments.py` uses `http.client` and `notify.py` uses `urllib.request`. Each has its own retry, timeout and back-off code, and each has been fixed separately:
- `1fd7dcc` fixed a connection leak in payments.
- `1e77a42` (timeout) and `15edf68` (back-off) fixed notify.

None of these fixes was carried over to the other file. The fix is one shared HTTP helper with retries, and the `cleanup` skill does this.

**3. (A distant third) `legacy/tax_tables.py`, `sales_tax()`.** It is 61 lines long, very complex and nested 9 levels deep. But nothing has touched it since it was ported in the first commit, it has never been fixed, and checkout only ever calls it with the category `"general"`. It costs nothing today. Do it only if next quarter includes tax-rule changes or tax categories at checkout, and then use `arch-design` to turn it into a table lookup.

If you have room for a third item that isn't from this ranking, consider checking whether the tests can catch a broken total (the `verify-loop` skill does this). Right now they would only notice the two totals disagreeing.