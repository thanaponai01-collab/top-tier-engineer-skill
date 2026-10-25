It's a small codebase (about 200 lines), so nothing here is hard to understand. But the place you're about to change is the worst-structured part of it, and nothing tests it. I'd call it a manageable mess: one function holds all the tangle, and it's surrounded by a few silent bugs a new discount will run into.

## Where it's tangled

**1. All pricing rules live in one function, `pricing.py:4-67`.** Line discounts, coupons, shipping and tax are all nested `if`s on raw dicts. The real problem isn't how it looks; it's that the order things happen in is the only thing defining how they interact, and that order is never written down:
- **Line discounts multiply together.** A bulk goods line with clearance gets 0.8 × 0.5 (`:18-26`). Is that intended, or should it be "best discount wins"? The code can't tell you.
- **Coupons see the total after line discounts.** So `SAVEx` checks `total > 50` against the already-discounted amount (`:34`).
- **US free shipping is decided after coupons** (`:46`). Any order-level discount you add can push an order under $35 and add a $5.99 shipping charge.
- **Tax is charged on discounted total plus shipping** (`:67`). So where your discount goes in the sequence changes the tax amount.
- **Only one coupon per order** (`order["coupon"]` is a single string). If the new discount is a coupon, it can't be combined with the others.

**Cost when you change it:** first you have to decide whether the new discount is per line or per order, and whether it applies before or after coupons, shipping and tax. Then you add another branch to the nest. Each time you do that, you have to work out its interactions with every existing branch in your head.

**2. Nothing records which discount was applied.** `compute_price` returns one rounded float. The exporters (`export_csv.py`, `export_json.py`) only know an `amount` that was saved earlier, and nothing in this repo creates invoices (`store.put` is never called). So if the new discount needs to appear on an invoice, there's nowhere to put it yet, and the two exporters copy the same formatting code, so you'd change both.

**3. The test is essentially missing.** `tests/test_pricing.py` has one case with no discounts (it passes). None of the roughly 15 branches is covered. This is the biggest cost: you can't refactor, or even add a branch, and know you haven't changed existing prices.

## Bugs you'll hit nearby (I reproduced each one)

- **Missing records silently get default values.** `store.get` (`store.py:18`) falls back to `models.blank_order()` for every table, including customers. An unknown customer becomes an order-shaped dict with no country, so it's charged international shipping and 20% tax. An unknown order is priced as an empty order and still gets charged shipping: `load_order('nope')` priced to **30.0** instead of an error.
- **`SAVE` coupons can make the total negative.** A $60 order with `SAVE100` (shipping off, US customer) priced to **-42.8**, and tax was applied to that negative amount.
- **`SAVE` followed by anything that isn't a number crashes.** `SAVEBIG` raises `ValueError` (`:35`).
- **Prices are calculated in floats** and only rounded at the end. Percentage discounts on top of each other will eventually give cent-level differences.

## Other mess, less relevant to discounts

- `store` and `models` import each other. It works today because each only uses the other inside functions, but it's fragile.
- `cli.py:22` reaches into `models.store._read()`, a private function accessed through another module's import.
- `static/app.js` calls a `/price` HTTP endpoint and expects `{total}`, but no server exists in this repo. Either it lives somewhere else or this file is orphaned.

## What I'd do before adding the discount

1. **Write tests for the current behaviour first**, one per branch in `compute_price`, including the shipping threshold and tax cases. That's maybe an hour of work and it makes everything after it safe.
2. **Split `compute_price` into stages:** `line_price(line, customer)`, `apply_order_discounts(total, order, customer, today)`, `shipping(...)` and `tax(...)`. Leave the logic unchanged; this just makes the order of operations visible.
3. **Add the new discount as one function** inside the stage it belongs to. If you expect more discount types later, have each discount return a `(name, amount)` pair so invoices can list them. That fixes problem #2 too.
4. **Fix the `SAVE` coupon bugs** while you're in that code. The `store.get` fallback is a separate fix, but it's worth putting on the list.

If the deadline is tight, you can skip step 2. Just don't skip step 1.