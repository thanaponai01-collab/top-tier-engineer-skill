No, it isn't strong enough. The suite is green and covers every line, but line coverage doesn't pin the boundaries or the `order_total` path. I ran 11 mutants of `shipping.py` against it. Four survived.

Run it from `fixture/` with `python -m unittest test_shipping`: 11 tests, all pass. (Running with `-I` fails only because isolated mode drops the working directory from `sys.path`, so the import breaks.)

**Bugs that get through**

1. **Free-shipping boundary off by one.** Change `subtotal >= FREE_SHIPPING_FROM` to `subtotal > FREE_SHIPPING_FROM`. The tests check 49.99 and 50.01 but never 50.00. SPEC.md says "$50.00 or more ship free", so `shipping_cost(50.00, 1)` should return 0.0 and this mutant returns 4.99.

2. **Heavy-fee boundary off by one.** Change `weight_kg > HEAVY_FROM_KG` to `>=`. The tests use 19.5 and 25 but never 20. SPEC.md says "heavier than 20 kg", so `shipping_cost(12.00, 20)` should return 4.99 and this mutant returns 19.99.

3. **Express is never tested through `order_total`.** Make `order_total` drop the express flag, i.e. call `shipping_cost(subtotal, weight_kg)`. Every `order_total` test uses the default `express=False`. `order_total(12.00, 1, express=True)` should be 25.45 and this mutant returns 17.95.

4. **Tax rounding is never tested with a fractional-cent tax.** Change the tax to truncation (`int(subtotal * TAX_RATE * 100) / 100`), or drop the rounding on the tax line. All the test subtotals (12.00, 100.00) produce whole cents of tax (0.96 and 8.00), so nothing distinguishes these. For example, `order_total(10.99, 1)` should be 16.86 (tax 0.88) and the truncating mutant returns 16.85.

**What the suite does catch:** the standard fee, the 49.99/50.01 pair, heavy fee on free orders, express on free orders, shipping not being taxed, the heavy fee being dropped from `order_total`, tax being applied to shipping, the final rounding in `order_total`, and a flipped `express` default.

**What would close the gaps:** add `shipping_cost(50.00, 1) == 0.0`, `shipping_cost(12.00, 20) == 4.99`, `shipping_cost(12.00, 21) == 19.99`, an `order_total` case with `express=True`, and an order_total case whose tax is a fractional cent (such as 10.99 → 16.86).

I haven't edited `fixture/`. Do you want me to add these tests and rerun the mutants?