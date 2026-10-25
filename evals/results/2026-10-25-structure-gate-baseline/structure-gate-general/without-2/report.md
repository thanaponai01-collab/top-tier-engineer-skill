It's not a mess overall. It's about 200 lines and most files are fine. The trouble is concentrated in one place, and that's exactly where you're working: **`compute_price` in `invoicing/pricing.py` is a single 67-line function covered by a single test.** That combination is what will make adding a discount expensive, more than the code style.

## Where it's tangled

**1. All discounts live in one nested `if` tree (`pricing.py:4-42`).** Line-level discounts (contract rate, service volume, bulk tiers, clearance, gift) and order-level coupons (`SAVEnn`, `FIRST`, `VIP`) are written inline, with nothing to plug a new one into. A new discount type means editing this function and choosing a spot in the branching.

**2. Where a discount sits in the order changes the price, and none of that ordering is written down.** The function runs in this sequence: line discounts → coupon → shipping → tax. So a new discount will also affect:
- **Shipping.** The US free-shipping threshold (`total < 35`, line 46) is checked *after* discounts, so a discount can push an order under $35 and add a $5.99 charge.
- **Tax.** Tax is charged on the subtotal *including shipping* (line 67).
- **Stacking.** Line discounts multiply each other: bulk ×0.8 plus clearance ×0.5 gives 40% of list price (I checked: 100 units at $10 come to $400). Only one coupon can apply because it's an `elif` chain. I can't tell from the code whether either behaviour is intended, and your new type has to choose one.

**3. Edge cases are unhandled, and a new discount will run into them.** I confirmed each of these:
- `SAVE100` on a $60 order gives **-40.0**. Nothing stops the total going negative.
- `SAVEBIG` **crashes** with `ValueError`, because the amount is parsed straight from the coupon string.
- A line with no `kind` is charged full price; `gift` is zeroed. Any unknown kind falls through without an error.
- A customer with `contract.rate == 0` is treated as having no rate (truthiness check on line 10).

**4. Prices use floats throughout** and are rounded only at the end. With percentage discounts, you'll see off-by-a-cent results at some point.

## Outside pricing (less relevant to this change, still worth knowing)

- **Unknown IDs don't raise an error** (`store.py:18`). An order or customer ID that doesn't exist comes back as `blank_order()`, including for *customers*. Pricing a nonexistent order for a nonexistent customer returns `30.0` (international shipping plus 20% tax). That will confuse you if you test the new discount against a typo'd ID.
- `store` and `models` import each other. It works today only because the import is used at call time.
- `cli.py:22` reaches into the private `models.store._read()`.
- `export_csv.py` and `export_json.py` contain the same invoice-formatting code twice.
- `static/app.js` fetches a `/price` endpoint that doesn't exist; there's no server, and the CLI prints a bare float. It looks like dead code.

## What it will cost you

The code change is small: a few lines in the `if` tree. The cost is that **you'll have no protection against breaking existing prices.** The one test covers plain goods, no shipping, a tax-free state. Contract rates, bulk tiers, clearance, all three coupons, VIP-in-December, shipping thresholds and tax rates are all untested. Changing anything in the shared `total` flow, such as where a discount applies or how they stack, could quietly change every other price.

## What I'd do, in order

1. **Write characterization tests first**: one case per existing branch (about 15–20 small tests), so you have a baseline before touching anything. This is the highest-value step.
2. **Decide the rules for the new type explicitly**: line-level or order-level, before or after the shipping threshold, whether it stacks with coupons, and a floor at zero.
3. Optionally, **pull discounts out** into a list of small functions (`apply_line_discounts`, `apply_coupon`) before adding yours. Once step 1 is done that's a cheap refactor, and every later discount becomes one function plus a test instead of another branch in the tree.

I wouldn't refactor without step 1, and I wouldn't bother with the store or export issues for this change. If you tell me how the new discount should behave, I can write the characterization tests.