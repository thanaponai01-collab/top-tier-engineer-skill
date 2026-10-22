**No, it isn't strong enough.** The suite passes on the current `shipping.py`, which matches SPEC.md, but I ran it against five small mutants of `shipping.py` and all five passed. Each mutant is a plausible bug that breaks the spec.

I ran the mutants on copies in a scratch directory, so `fixture/` is unchanged.

**Mutants that get through (all report `OK`):**

1. **Free-shipping threshold is strict.** `subtotal >= FREE_SHIPPING_FROM` becomes `subtotal > FREE_SHIPPING_FROM`. SPEC.md says "$50.00 or more ship free", but the tests only use 49.99 and 50.01, so an order of exactly $50.00 is charged $4.99 when it should ship free.
2. **Heavy threshold is inclusive.** `weight_kg > HEAVY_FROM_KG` becomes `>=`. SPEC.md says "heavier than 20 kg", but the tests only use 19.5 and 25, so a 20 kg parcel gets a $15 fee it shouldn't.
3. **`order_total` drops express.** `order_total` calls `shipping_cost(subtotal, weight_kg)` without `express`. Every `order_total` test uses the default `express=False`, so the express fee never reaches the total. A $12 express order should total $25.45 and this returns $17.95.
4. **Heavy fee disappears on express orders.** `if weight_kg > HEAVY_FROM_KG:` gets `and not express`. No test combines heavy and express.
5. **Express disappears on heavy orders.** `if express:` gets `and weight_kg <= HEAVY_FROM_KG`. Same gap: no heavy-plus-express test.

**Why the suite misses them:** the tests check each rule in isolation at mostly one side of each boundary. There is no test at a threshold value, no test that passes `express` through `order_total`, and no test where two surcharges apply together.

**Other observations:**
- Tax is well covered. Two different subtotals and one heavy-shipping total would catch a tax-on-shipping bug. I also checked that 2-decimal subtotals cannot land on a half-cent tie, so the rounding mode can't be tested with valid inputs.
- The tests only assert exact values, so they would catch a wrong number. They just don't cover the places where the code is most likely to be wrong.

**What would close the gaps:**
- `shipping_cost(50.00, 1)` → `0.0`
- `shipping_cost(12.00, 20)` → `4.99`, and `shipping_cost(12.00, 20.01)` → `19.99`
- `order_total(12.00, 1, express=True)` → `25.45`
- `shipping_cost(12.00, 25, express=True)` → `27.49`
- `order_total(50.00, 1)` → `54.00`

I haven't edited `fixture/`. Do you want me to add these tests to `test_shipping.py` and confirm that each of the five mutants now fails?