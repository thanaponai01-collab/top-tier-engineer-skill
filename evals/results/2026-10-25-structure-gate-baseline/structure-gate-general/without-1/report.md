It's mixed. The project is small (about 200 lines) and most of it is fine. The part you're about to change is the messy part, and it has almost no tests.

## Where it's tangled

**1. `pricing.py:4-67`: one 60-line function does four jobs.** `compute_price` handles line pricing, coupons, shipping and tax in sequence, all modifying one `total` variable. Discounts live in two places with different rules:
- **Line-level discounts** (lines 8–29) are nested `if`s by `kind`. Rules pile on top of each other: bulk and clearance multiply together, so bulk + clearance comes to 0.4×.
- **Order-level coupons** (lines 32–42) are an `if/elif` chain on the coupon string, and an order can hold only one coupon.

Neither has a hook to plug a new type into. You'll be adding another branch to the chain.

**2. The order of the steps changes the result, and nothing documents it.** Coupons run before shipping, and the US free-shipping check (`total < 35`) looks at the discounted total. I ran it: a $38 order with `FIRST` drops to $32.30, picks up $5.99 shipping, and comes to $38.29. The customer gets almost nothing off. Tax is also applied after shipping, so shipping gets taxed. Depending on where your new discount goes in the sequence, it will change shipping and tax too.

**3. The coupon parsing is fragile.** These are the existing bugs I confirmed by running it:
- `SAVE100` on a $60 order gives **-$40.00**. Nothing stops the total going below zero.
- `SAVEBIG` raises `ValueError`. Any code starting with "SAVE" is assumed to end in a number.
- A coupon that doesn't match any rule, or doesn't apply to this customer, does nothing silently.

**4. Customer fields are read loosely everywhere.** It checks `customer.get("contract")`, `"wholesale"`, `"vip"`, `"orders"`, `"country"`, `"tax_exempt"` and so on, with no schema. A typo just makes a rule quietly not apply. The data also comes in broken: `store.get` (`store.py:18`) falls back to `models.blank_order()` for **every** table. A customer ID that doesn't exist comes back as an empty order dict (I checked). That customer then gets priced as a non-US customer with no country: $25 shipping and 20% tax, and no error.

## Smaller tangles that won't affect your discount work
- `models.py` and `store.py` import each other. It only works because the cross-reference happens at call time.
- `cli.py:22` reaches through `models.store._read()` into a private function.
- `export_csv.py` and `export_json.py` repeat the same field-formatting loop. Change one and you have to change the other.
- `static/app.js` calls `/price` and reads `body.total`, but no HTTP server exists in the code, and the CLI prints a bare number. That file is either dead code or depends on something outside this folder.

## What it will cost you
- **Tests are the biggest cost.** `tests/test_pricing.py` has one test (goods, no shipping, a tax-free state). It covers none of the discounts, coupons, shipping or tax branches. If you change `compute_price` now, nothing will catch a regression. Run the tests with `python -m unittest tests.test_pricing`; `discover` fails because `tests/` has no `__init__.py`.
- **The new type itself is cheap.** It's another `elif`, maybe 5–10 lines.
- **The hidden cost is in what it affects.** You'd need to decide where it goes in the order of steps, whether it can combine with other discounts, whether it can push the total negative, and how it interacts with the $35 shipping threshold. Today none of those answers are written down; they just follow from the order of the code.

## What I'd do, in order
1. Write tests that pin down the current behaviour of `compute_price`: one per discount, coupon, shipping and tax branch, including the odd cases above. Decide which of those are bugs and which are intended. That's about an hour of work.
2. Split it into `line_price(line, customer)`, `apply_coupon(total, code, customer, today)`, `shipping(...)` and `tax(...)`, so the order of steps is visible in a few lines. Since this is a mechanical change, the tests from step 1 make it safe.
3. Add your discount as its own function in the right place. Add a floor at zero, and validate coupon codes so bad ones raise an error instead of being ignored.

If your new type is a coupon, steps 1 and 3 are enough. If it's a line-level or stacking discount, do step 2 first, or you'll be adding one more layer to the nested `if`s.