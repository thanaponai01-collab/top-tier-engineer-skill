No, it isn't strong enough. Both boundaries in the spec are untested, and a bug at either one passes all 11 tests.

I checked this by making each change to a copy of `shipping.py` and running `test_shipping.py` against it. Both stayed **green**:

**1. Free-shipping threshold: `>=` changed to `>`** (`shipping.py:11`)
- SPEC rule 1 says "$50.00 **or more** ships free."
- The tests check 49.99 and 50.01 but skip exactly 50.00.
- With the bug, `shipping_cost(50.00, 1)` returns **4.99** instead of 0.0, and `order_total(50.00, 1)` returns **58.99** instead of 54.00. The customer pays for shipping they should get free.

**2. Heavy-fee threshold: `>` changed to `>=`** (`shipping.py:13`)
- SPEC rule 2 says "heavier than 20 kg," so exactly 20 kg gets no fee.
- The tests check 19.5 and 25 but skip exactly 20.
- With the bug, `shipping_cost(12.00, 20)` returns **19.99** instead of 4.99, a $15 overcharge.

These are the most likely edits for someone to make by mistake, and full line coverage can't catch them because the boundary lines run either way.

Fix: add these four assertions.

```python
self.assertEqual(shipping_cost(50.00, 1), 0.0)
self.assertEqual(order_total(50.00, 1), 54.00)
self.assertEqual(shipping_cost(12.00, 20), 4.99)
self.assertEqual(shipping_cost(80.00, 20), 0.0)
```

The current `shipping.py` gets both boundaries right, so these will pass now and fail if either bug is introduced. The rest of the spec is covered: every other rule has a test pinning its amount, including express on free orders and untaxed shipping.