The codebase is small (about 200 lines) and mostly fine. The one part that matters for your change is `invoicing/pricing.py`, and that part is tangled and essentially untested. Adding a discount type won't be big work, but it's easy to get wrong without noticing.

## Where it's tangled

**1. All pricing logic is in one function, and the order of its steps matters.** `compute_price` (`pricing.py:4-67`) runs line discounts, then coupons, then shipping, then tax, all in one block. Each step reads the running `total` left by the step before. That means a discount changes more than the price:
- **US free shipping** is decided on the total *after* discounts (`pricing.py:46`). I ran a $36 order with `FIRST`: it dropped below $35, picked up the $5.99 shipping, and came to $36.59 instead of $30.60.
- **`SAVE` coupons only apply when the total is over 50**, and that's checked after line discounts (`pricing.py:34`). A new line-level discount can quietly switch a coupon off.

So for a new discount, the hard question is *where in that sequence it goes*, and right now the code doesn't make that order explicit anywhere.

**2. Discounts live in two places and follow different rules.**
- **Line discounts** (`pricing.py:8-29`) are nested `if` statements by `kind`, and they multiply together. Bulk plus clearance comes out to `0.9 × 0.5`. There's no cap on stacking.
- **Coupons** (`pricing.py:32-42`) are an `if/elif` chain, so an order gets at most one coupon. If a coupon's conditions aren't met, it's ignored without any message.

Depending on what your new discount is, it goes into one of these two blocks, and each has its own stacking behaviour. Decide which one you want before writing it.

**3. No schema, only dict keys.** Customer settings (`contract.rate`, `wholesale`, `vip`, `orders`, `tax_exempt`, `country`, `state`) and line settings (`kind`, `bulk`, `clearance`) are all read with `.get()` and aren't defined anywhere. If you misspell a new flag, the discount just never applies, with no error.

**4. The result is a single number.** `compute_price` returns one rounded float and doesn't record which discounts were applied. If the new discount needs to show up on an invoice, you'll have to change that return value. Its callers are `cli.py:20` and, apparently, `static/app.js:5`, which expects `body.total` from a `/price` endpoint. That endpoint doesn't exist in this code, so whatever serves it lives elsewhere and you'd need to find it. The two exporters (`export_csv.py` and `export_json.py`) contain the same row-building code, so an invoice discount column would mean editing both.

## Existing bugs you'd be building on
I ran these to confirm them:
- `SAVE100` on a $60 order returns **-40.0**. Nothing stops a total from going negative, and shipping and tax are then added to the negative amount.
- `SAVEBIG` on an order over $50 crashes with `ValueError`, because the code does `float(code[4:])` without checking the text.
- `store.get` (`store.py:18`) uses `blank_order()` as the fallback for *every* table. A missing customer becomes an order-shaped dict, and a missing order gets priced as an empty order instead of raising an error.
- `models` and `store` import each other. It works today only because each one uses the other at call time rather than at import time.

## Tests
There is one test (`tests/test_pricing.py`). It covers plain goods, no shipping, and a state with no sales tax. **No discount, coupon, shipping or tax path is tested.** Also, `python -m unittest` on its own finds 0 tests because `tests/` has no `__init__.py`. Running `python -m unittest tests.test_pricing` works. That's the biggest cost of your change: you can't currently tell whether you broke an existing discount.

## What it will cost, and what I'd do
For a simple discount added to one of the two blocks, expect about 10 lines of code. The bigger job is checking how it interacts with the shipping threshold, the `SAVE` threshold and the existing stacking, and right now you'd be checking that by hand.

Here's how I'd do it, roughly half a day of work:
1. **Write characterization tests first.** Cover each line discount, each coupon, the $35 shipping cutoff, and one tax case per country. That locks in current behaviour, bugs included.
2. **Split `compute_price` into four functions:** `line_price`, `apply_coupon`, `shipping` and `tax`. At 67 lines this is a quick, low-risk job, and it makes the step order visible in one place.
3. **Then add the new discount** to the right function, and decide on purpose whether it stacks with other discounts and whether it should affect free shipping.
4. You can fix the negative total and the `SAVE` crash while you're in there. That changes behaviour, so make it a separate commit.

Tell me what the new discount does (per line or per order, and how it should stack) and I can do steps 1 and 2.