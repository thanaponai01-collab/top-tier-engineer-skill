**It's tangled in places, and the worst spot is exactly where your new discount will go.** All the pricing logic sits in one function, `compute_price`. Everything else is small and fine apart from two smaller structural problems.

**What was measured:** 201 lines of code. A parser measured 93% of them (187 lines, all the Python, with full complexity checks). The other 14 lines are `fixture/static/app.js`. No parser here handles JavaScript, so I read that file by hand.

| Where | Measured | What it costs you when you add a discount |
|---|---|---|
| `invoicing/pricing.py:4` `compute_price` | 64 lines, complexity 32, nesting 6 | Line-item discounts, coupons, shipping and tax are all in one function. There are 9 line-level discount branches (service, goods, bulk, clearance, gift) and 3 coupon branches (`SAVE<n>`, `FIRST`, `VIP` with a December special case). A new type means adding another branch either to the line loop or to the coupon `elif` chain. The order matters but nothing states it: line discounts apply first, then coupons, then shipping (which depends on the discounted total, e.g. the US $35 free-shipping cutoff), then tax. Coupons also can't be combined, because only the first match in the `elif` chain applies. **The real cost is that only one test exists** (plain goods, no shipping, Oregon). None of the roughly 30 paths through the function is protected when you edit it. |
| Import cycle: `models` ↔ `store` | 2 modules | It imports fine in either order today (I checked). The reason it exists is a small bug: `store.get` falls back to `models.blank_order()` for *any* missing key. So an unknown customer comes back as an order-shaped dict instead of an error (I confirmed `{'lines': [], 'coupon': None, 'ship': True, …}`). A discount based on customer data like `vip`, `orders` or `wholesale` would quietly treat that as a real customer. |
| Copied block: `export_csv.py:6` / `export_json.py:6` | 2 identical copies | The 5 field calculations are copied line for line. If invoices need to show the discount, you have to make the same edit in both files, and they'll drift apart over time. |
| `static/app.js` (read by hand) | 14 lines | It only fetches `/price` and displays `total`, so a discount change doesn't touch it. However, nothing in the Python code serves `/price`, so the page's backend is missing. |

The other 12 of the 13 functions are under every threshold. `cli.py:22` also reaches into `models.store._read()` directly, but that doesn't affect discounts.

**Before adding the discount, I'd do this:**
1. Write characterization tests for `compute_price` that cover each line kind, each coupon, and each shipping/tax region. Without them you have no way to tell whether the new branch broke an old one.
2. Pull the line-discount and coupon logic out into small functions (or a table of rules) that run in a stated order. Then the new discount type is one new rule.
3. Optionally, make `store.get` raise on a missing customer so customer-based discounts can't see a fake one.

I only reported; nothing was changed. The run's scratch notes in `.structure/` have been deleted. If you want CI to stop this shape getting worse, `structure-report.py --write-baseline` records today's findings as a baseline, and `--baseline` then fails only when a finding is new or worse.