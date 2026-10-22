**No, it isn't strong enough.** The suite is green (11 tests pass with `python -m unittest test_shipping` run from `fixture/`), and every line runs. But I mutated `shipping.py` in a scratch copy and 6 of 9 meaningful bugs got through. The gaps are at boundaries and in combinations of features that no test covers.

**Bugs that pass the gate (verified by running them):**

1. **Free-shipping threshold becomes strict.** `subtotal > 50` instead of `>= 50`. `shipping_cost(50.00, 1)` returns 4.99; the spec says it should be 0.0. No test uses exactly 50.00. The tests only use 49.99 and 50.01.
2. **Heavy threshold becomes inclusive.** `weight_kg >= 20` instead of `> 20`. A 20 kg parcel gets the $15 fee, but the spec says "heavier than 20 kg". The tests only use 19.5 and 25.
3. **Heavy threshold moves anywhere between 19.5 and 25.** For example `weight_kg > 24`. A 22 kg parcel silently skips the fee. Nothing tests weights between 19.5 and 25.
4. **Heavy fee dropped on express orders.** `if weight_kg > HEAVY_FROM_KG and not express:`. No test combines heavy and express. The correct result for `shipping_cost(12, 25, express=True)` is 27.49.
5. **`order_total` ignores express.** Passing `express=False` inside `order_total`. Every `order_total` test uses the default, so the express surcharge never reaches the total. The correct result for `order_total(12, 1, express=True)` is 25.45.
6. **Tax truncated instead of rounded.** `int(subtotal * 0.08 * 100) / 100`. Every tested subtotal produces an exact cent amount (12.00 and 100.00), so the two agree. `order_total(10.19, 1)` should be 16.00 (tax 0.82); the truncated version gives 15.99.

Mutants that were caught: dropping the final `round`, taxing shipping, and applying express only to paid shipping.

**Tests that would close these gaps** (each one kills a mutant above):

```python
def test_exactly_at_free_shipping(self):
    self.assertEqual(shipping_cost(50.00, 1), 0.0)

def test_exactly_at_heavy_threshold_has_no_fee(self):
    self.assertEqual(shipping_cost(12.00, 20), 4.99)

def test_just_over_heavy_threshold_adds_fee(self):
    self.assertEqual(shipping_cost(12.00, 20.5), 19.99)

def test_heavy_and_express_stack(self):
    self.assertEqual(shipping_cost(12.00, 25, express=True), 27.49)

def test_express_reaches_order_total(self):
    self.assertEqual(order_total(12.00, 1, express=True), 25.45)

def test_tax_rounds_half_up_to_cent(self):
    self.assertEqual(order_total(10.19, 1), 16.00)
```

Also worth knowing: `python -I -m unittest` fails with an ImportError because isolated mode drops the working directory from `sys.path`. If your merge gate uses `-I`, it will fail for setup reasons, not because of the code.

I didn't change anything in `fixture/`. The mutants were run in a temp directory. Do you want me to add these tests to `test_shipping.py`?