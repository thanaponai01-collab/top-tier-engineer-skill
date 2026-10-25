The code is small (about 210 lines), so it isn't a mess. But the discount logic is tangled in the specific way that makes adding a discount risky, and there are almost no tests to catch a mistake.

## What's fine

- `compute_price` (`invoicing/pricing.py:4`) is a pure function. It takes `order`, `customer` and `today` and does no I/O, so it's easy to test.
- The stages always run in the same order: lines, then coupon, then shipping, then tax.

## Where it's tangled, and what that costs you

**1. Discounts live in two places with different rules.**
- **Per-line discounts** (`pricing.py:6-30`) are nested `if`s keyed on `kind`: service contract rates, goods bulk tiers, clearance, gift. They stack by multiplying; for example, bulk plus clearance gives 0.8 × 0.5.
- **Order-level coupons** (`pricing.py:32-42`) form one `if/elif` chain, so only one coupon can ever apply. A coupon that doesn't qualify is silently ignored.

*Cost:* before you write any code you have to decide whether the new discount is per-line or per-order, whether it stacks with the others, and where it goes in that order. None of this is written down; it's only implied by the `if` nesting.

**2. Discounts affect shipping and tax.** The US free-shipping rule (`total < 35`, line 46) checks the total *after* discounts, and tax is charged on the discounted total plus shipping. A new discount can push an order back under $35, which adds $5.99 shipping, and then tax applies to that. You'll need tests for orders near that threshold.

**3. Existing coupon bugs you'll run into.** I confirmed these by running them:
- `SAVE100` on a $60 order returns **-36.39**. The fixed discount has no floor, so the total goes negative, then shipping is added and tax is applied to the negative amount.
- `SAVEBIG` raises `ValueError`, because the code does `float(code[4:])` (line 35) with no check.
- Codes are parsed by string prefix. If your new code starts with `SAVE`, the `SAVE` branch will claim it.

**4. Mistakes don't raise errors.** Everything reads plain dicts with `.get()`, so a typo just fails quietly. A line with `"kind": "Goods"` (capital G) gets no discounts and is charged full price. A misspelled customer flag like `"wholsale"` does nothing. All the rates and thresholds are hard-coded numbers.

**5. Test coverage is nearly zero.** There's one test (`tests/test_pricing.py`). It passes, but it covers only goods, with no coupon, no shipping, and a state with no tax. **This is the biggest cost.** Nothing will tell you if your change breaks an existing discount.

## Not about discounts, but worth knowing
- **Missing records turn into fake ones.** `store.get` falls back to `models.blank_order()` for *any* table (`store.py:18`). A customer ID that doesn't exist becomes an order-shaped dict with no country, and a missing order is priced at **$30.00** (international shipping plus 20% tax) instead of raising an error.
- **Circular import:** `store` and `models` import each other. It works today only because `blank_order` is looked up when called, not at import time.
- **Duplicate formatting code:** `export_csv.rows_for` and `export_json.records_for` repeat the same field formatting line for line.
- **`cli.py:22`** reaches into `models.store._read()`, a private function.
- **`static/app.js`** calls `/price`, but no HTTP endpoint exists in this code.
- Money is calculated in floats and rounded only at the end.

## Before you add the discount
1. **Add characterization tests first.** Pin down how each line kind, each coupon and the US/CA/other branches behave today, plus a few combined cases such as bulk + clearance + VIP in December, and an order near $35.
2. **Decide and record the stacking rule** for the new discount: per-line or per-order, and whether it combines with coupons.
3. If it's a coupon, a small refactor is worth it: turn the `elif` chain into a table of coupon handlers, floor the total at 0, and validate the `SAVE` amount. If it's per-line, add it inside the right `kind` branch and test it alongside bulk and clearance.

If you want, I can write the characterization tests now. That's the cheapest step and the one that protects the change most.