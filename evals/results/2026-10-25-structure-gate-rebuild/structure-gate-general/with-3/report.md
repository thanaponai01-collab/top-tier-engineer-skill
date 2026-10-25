**It's a mess in places, and the worst place is right where you'll add your discount.** The codebase overall is small and mostly fine: 12 of 13 functions are under every threshold. The tangle is concentrated in `compute_price`.

**How much was measured:** 201 code lines, 93% parsed (187 lines; the Python got full analysis). The other 14 lines are `fixture/static/app.js`, which has no parser here, so I read it by hand. That makes it a reading, not a measurement. `structure-gate` finished with all three stages passing.

| Finding | Measured | What it costs you |
|---|---|---|
| `fixture/invoicing/pricing.py:4` `compute_price` | 64 lines, complexity 32, nesting 6 | See below. This is the main cost. |
| Import cycle `models` ↔ `store` | 2 modules | `store.get` falls back to `models.blank_order()` for every table. I ran it: a missing customer loads as an order-shaped dict (`{'lines': [], 'coupon': None, ...}`) and gets priced anyway instead of raising an error. `cli.py:22` also reaches past this into `models.store._read()`. If your discount needs a new table or customer field, you'll first have to work out which module owns the defaults. |
| Copied block in `export_csv.py:6` / `export_json.py:6` | 2 copies | The 5-field invoice normalisation is written twice. If the discount should appear on invoices, you have to change both identically, or CSV and JSON exports will disagree. |
| `static/app.js` (read, not measured) | 14 lines, 2 functions, 1 listener | It has no pricing logic. But it calls a `/price` HTTP endpoint that nothing in `invoicing/` serves; the CLI is the only entry point. |

**What adding a discount type will cost you in `compute_price`:**
- **Discounts aren't in one place.** Line-level discounts (lines 8–29, branching on line kind, contract, bulk and clearance) and order-level coupons (lines 32–42) are separate branches inside the same function as shipping and tax. There's no discount abstraction. A new type is another nested `elif`, and you have to decide by hand where it goes relative to coupons, the free-shipping cutoff (`total < 35`, which is checked after discounts) and tax.
- **Coupons can't be combined, and order matters.** Only one coupon can apply, picked by the `elif` order. Unknown codes are silently ignored, with no error.
- **There's an existing bug.** A `SAVE<n>` coupon can push the total below zero. I ran it: `SAVE100` on a 60.00 order prices at **-40.0**. Any new subtract-a-fixed-amount discount will inherit this unless you add a floor.
- **Almost nothing is tested.** `tests/test_pricing.py` has one test, plain goods with no discount, and it passes. None of the discount, coupon, shipping or tax branches is tested, so a refactor or a new branch can break existing pricing without anyone noticing.

**Suggestion before adding the discount:** first write characterisation tests for the existing discount and coupon branches. Then pull discounts out of `compute_price` into an ordered list of small functions (line discounts, then order discounts), and your new type becomes one more entry. While you're in there, add a floor at 0 so discounts can't take the total negative.

**Not covered:** `app.js` was read, not measured. Nothing tests how the code actually behaves, apart from the one test and the two cases I ran. I didn't change any code, and I deleted the `.structure/` scratch folder.