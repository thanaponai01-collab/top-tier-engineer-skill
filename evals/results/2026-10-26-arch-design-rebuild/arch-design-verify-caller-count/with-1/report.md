**Yes, it's safe to remove.** The interface is `ShippingCalculator` in `shipping/base.py:8`, and only two lines in the repo have to change. I deleted it in a temporary copy and both programs that use shipping gave the same totals before and after.

## Audit result (arch-design, all checks passed)

**Overall: the structure is clean.** The only finding is this one leftover class, kept "in case a second carrier is ever needed" (`base.py:3`).

**Why it looks unused, and why that's mostly right:**
- `ShippingCalculator` is named in exactly one other file: `shipping/flat_rate.py:1` (the import) and `:4` (`class FlatRateCalculator(ShippingCalculator)`).
- Nothing anywhere checks the type (no `isinstance` or `issubclass` calls). All it provides is a `quote()` that raises `NotImplementedError`, and `FlatRateCalculator` replaces that anyway.
- The real users reach the subclass indirectly, so a search for the class name won't find them:
  - `checkout/cart.py:1,5` gets it through `get_calculator("flat")`.
  - `jobs/reprice.py:2,6` imports `get_calculator` under another name (`pick_calc`), then calls `pick_calc("flat")`.
  - `shipping/registry.py:3` links the text key `"flat"` to `FlatRateCalculator`.

  These only ever call `.quote(order)`, so they keep working without the base class and need no edits.

**What has to change:**
1. In `shipping/flat_rate.py`, delete line 1 and change line 4 to `class FlatRateCalculator:`.
2. Delete `shipping/base.py`.

**Test command** (run from `fixture/`; it passed before and after the change):
```
python -B -c "from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{'subtotal':10}]; r(o); assert t({'subtotal':10})==15.0 and o[0]['shipping']==5.0; print('ok')"
```

**Easy to undo:** nothing saved or published depends on the class name. If a second carrier does arrive, the `CALCULATORS` dict in `registry.py:3` is already where new carriers plug in. Adding one is a new class plus one dict entry, and the base class doesn't help with that. Recreating it later would mean writing three lines again.

**Keeping it** (as is, or as a `typing.Protocol` type hint) costs little but does nothing today.

**One thing to check before merging:** I could only see `fixture/`. If any code outside it imports `shipping.base` (tests, plugins, another repo), that code will fail to import. Search those places too.

**Other problems I noticed while reading:**
- `get_calculator` raises an unexplained `KeyError` if it gets a name it doesn't know (`registry.py:7`).
- Shipping prices are stored as floats (`5.00`) and added to the subtotal as floats, which can produce rounding errors.
- There are no tests. The command above is the only check on this behaviour.

I didn't change anything in `fixture/`. Should I go ahead with the removal, or would you rather keep the base class as a `Protocol`?