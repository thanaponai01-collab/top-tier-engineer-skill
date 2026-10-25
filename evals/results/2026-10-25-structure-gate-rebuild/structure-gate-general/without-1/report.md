It's small (about 200 lines) and you can read all of it quickly, but the part you're about to change is the most tangled part. The good news is that the tangle is in one place: `compute_price` in `invoicing/pricing.py`. The rest of the code mostly doesn't affect a discount change.

## Where it's tangled

**1. Every discount is hard-coded into one 60-line function.** `pricing.py:4-67` handles line pricing, line discounts, coupons, shipping and tax in a single pass of nested `if`s, with nothing broken out. Discounts appear at two levels:
- **Line-level** (lines 8-29): the discount depends on `kind` (service/goods/gift) mixed with customer attributes like `contract`, `contract.rate` and `wholesale`, plus line flags like `bulk` and `clearance`.
- **Order-level** (lines 32-42): coupons are checked by string-matching codes in an `if/elif` chain. `SAVE<n>` subtracts a fixed amount, while `FIRST` and `VIP` multiply.

No function says "apply discounts", and no discount type is defined anywhere else. A new discount means adding another branch somewhere in that chain.

**2. The rules for combining discounts are never written down.** They follow from where each branch happens to sit:
- Line discounts multiply together. A bulk clearance line gets 0.9 × 0.5 = 45% of list price. I checked: $10 becomes $4.50.
- Because of the `elif`, an order can use only one coupon.
- Coupons apply after line discounts. `SAVE`'s `total > 50` check therefore uses the already-discounted total.
- A contract `rate` replaces the line price completely. `unit_price` is ignored.

Your new discount has to choose a position in this sequence, and wherever you put it, it will interact with everything above and below. You'll need to decide on purpose whether it combines with coupons, with bulk, and with clearance. Nothing in the code will tell you.

**3. Discounts feed into shipping and tax.** Shipping comes after discounts, and the US free-shipping cutoff (`total < 35`, line 46) uses the discounted total. So a discount can add a $5.99 shipping charge. Tax is then charged on the total including shipping. Any new discount changes shipping and tax for some orders, whether or not you want it to.

**4. The existing discounts already have bugs.** You'll be building next to these:
- `SAVE100` on a $60 order gives **-$34.01**. Nothing stops the total going below zero.
- `SAVEME` (or any `SAVE` code without a number) **crashes** with `ValueError`.
- Unknown line `kind`s are charged full price without any warning.

**5. There's almost no safety net.** `tests/test_pricing.py` has one test: plain goods, no shipping, a state with no sales tax. It passes, but no coupon, bulk, contract, shipping or tax path is tested. Any change to how discounts interact will go unnoticed unless you test it yourself.

**6. The output is one rounded float.** `compute_price` returns only a total, and the exports show only `amount`. If the new discount needs to appear on the invoice as its own line, you'll have to change the return shape first. That change spreads to `cli.py`, the stored invoices and both exporters.

## Other problems that won't block you

- **Missing records are filled with fake data.** If a key is missing in *any* table, `store.get` returns a blank *order* (`store.py:18`). An unknown customer ID becomes `{'lines': [], 'coupon': None, ...}`, so it has no country, gets the 20% tax rate and is charged international shipping, with no error.
- **`store` and `models` import each other.** It works, but only because the imports run at call time.
- **`cli.py:22` reaches into `models.store._read()`**, a private function, and assumes an `invoices` table that the default empty database doesn't have.
- **`export_csv.py` and `export_json.py` repeat the same normalization code.** This only matters if discount details need to appear in exports, and then you'd have to change it twice.
- **`static/app.js` calls a `/price` endpoint and expects `{total}`.** No such server exists. It's either dead code or lives somewhere else.

## What the change will cost

- **If you just add another branch:** about an hour of work, but each branch makes the next change harder, and you won't know whether you've changed the price of existing orders.
- **Doing it properly** is maybe half a day to a day:
  1. First, write tests for the current behaviour: each discount, the combinations, the shipping cutoff and tax. That fixes today's outputs in place.
  2. Move discounts out of the function into ordered steps. For example, a list of line rules and a list of order rules, each taking `(order, customer, today)` and returning an adjustment, with the combining rules stated explicitly.
  3. Add your discount as one new step.
  4. Decide whether to fix the negative total and the `SAVE` crash now. Fixing them changes outputs, so do it on purpose and not as a side effect.

I'd do steps 1 and 2 before adding the discount. With only one test, the risk isn't writing the new discount. It's quietly changing the price of orders that never use it.