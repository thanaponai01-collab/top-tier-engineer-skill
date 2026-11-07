The checkup is done and the gate passed (`CHECKUP-GATE: done`). I didn't change any code, and I deleted the temporary `.checkup/` folder afterwards, so the working tree is clean.

**What was measured:** 13 tracked files (12 of them code) and all 13 commits. The code parser read 100% of the 204 code lines.

## How well it's structured

| Property | Rating |
|---|---|
| Easy to find things | not checked (there's no `FEATURES.md` mapping each feature to its code) |
| One change in one place | **poor** |
| Dependencies point one way | good (no `layers.txt` defines which layer may import which, so layer rules weren't checked) |
| Deep modules, narrow doors | in places |
| One way per job | **poor** |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked (that needs the tests run against deliberately broken code) |

Overall the code is small and mostly tidy. Its real problem is duplication, and the git history shows it causing bugs again and again.

## What to fix first

**1. Put the pricing rule in one place (`shop/cart.py` and `shop/receipt.py`).** Both files hold their own copy of the discount constants and the total calculation, and neither imports the other. They changed together in 5 of the 13 commits, and they drifted apart each time someone edited only one:
- `82b04a5` changed the member discount in the cart only, so `716a01b` had to fix the receipt.
- `fa4e4f0` fixed the two copies rounding differently.
- `6c240fd` fixed the bulk discount percentage in both.
- `ba474a1` and `27069c6` are pricing changes that had to be made twice.

The fix is a single pricing function that both the cart and the receipt call. Any pricing change you plan for next quarter will hit this.

**2. Use one HTTP and retry approach (`shop/payments.py` and `shop/notify.py`).** Payments uses `http.client` and email uses `urllib.request`. Retry logic was built separately in each (`a16bb3b`, `774a33f`), and each one later needed its own fix:
- `1fd7dcc`: payment retries leaked connections.
- `1e77a42`: order emails timed out under load.
- `15edf68`: email retries hammered the webhook, so they got exponential backoff.

Payments still waits a fixed, slowly growing time between retries instead of backing off. The next problem with either outside service will need fixing twice again.

**3. No third fix is warranted yet.** The only other finding is `sales_tax()` in `legacy/tax_tables.py`. It is the ugliest code in the repo: 61 lines, complexity 25, nested 9 deep. But no commit has touched it since the initial import, it has never needed a fix, and only `shop/checkout.py` uses it. Rewriting it now would spend effort without making any upcoming change easier. Move it to the top of the list as soon as you plan to touch tax rates or regions.

For a third item next quarter, I'd do one of the two areas the checkup couldn't measure. First choice: check whether the tests would actually catch a broken total (the verify-loop skill does this). `tests/test_totals.py` was added after the cart/receipt drift, and it's the main safeguard for fix 1. Second choice: write a `FEATURES.md` so "easy to find things" can be rated.

The checkup names two skills for the fixes: untangle for #1 and cleanup for #2. Neither is installed in this environment.