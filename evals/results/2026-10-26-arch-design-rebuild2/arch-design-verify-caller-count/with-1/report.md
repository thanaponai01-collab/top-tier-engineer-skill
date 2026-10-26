Yes, it's safe to remove `ShippingCalculator`, but it isn't actually unused. Deleting only `shipping/base.py` would break both checkout and the nightly reprice job. The gate passed (`ARCH-GATE: done`), and nothing in `fixture/` was changed.

**Verdict: clean.** The code is small and well laid out. Its one extra piece is a base class kept "in case a second carrier is ever needed," and it has a single implementation.

**Why it looks unused but isn't.** No code calls `ShippingCalculator` directly: nothing uses `isinstance` on it, puts it in a type hint or looks it up by name. But `shipping/flat_rate.py:1` imports it and `shipping/flat_rate.py:4` subclasses it. Everything else reaches that module indirectly:
- `shipping/registry.py:1` imports `FlatRateCalculator`.
- `checkout/cart.py:1` imports `get_calculator`.
- `jobs/reprice.py:2` imports it under another name, `get_calculator as pick_calc`. A search for `get_calculator(` misses this one.

Deleting only `base.py` makes `flat_rate.py` fail to import, and that failure takes down both checkout and the reprice job.

**The move: delete `shipping/base.py::ShippingCalculator`** (easy to undo, so no design fork is needed)
1. In `shipping/flat_rate.py`, delete line 1 (`from shipping.base import ShippingCalculator`) and change line 4 to `class FlatRateCalculator:`.
2. Delete `shipping/base.py`.

Nothing else changes. `registry.py`, `cart.py` and `reprice.py` stay as they are.

- **Proof:** run this from the `fixture/` root. In a throwaway copy it printed `ok` both before and after the two steps:
  ```
  python -B -c "from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{'subtotal':10}]; r(o); assert t({'subtotal':10})==15.0 and o[0]['shipping']==5.0; print('ok')"
  ```
  Afterwards, a search for `ShippingCalculator` finds nothing.
- **What already does the job:** the `CALCULATORS` dict in `shipping/registry.py:3` already chooses which calculator to use. That is where a second carrier would be added, so the base class adds nothing.
- **Not taken:** keeping the base class, or swapping it for a `typing.Protocol`. Either would be a second definition of the calculator interface that no caller checks.
- **Cost if wrong:** if a second carrier arrives, bringing back a base class is one new file plus one line per calculator. Nothing stored or public depends on it.

**Seen in passing (not structural):**
- `get_calculator` in `registry.py:7` raises `KeyError` for an unknown name.
- `quote` in `flat_rate.py:8` returns money as a float (`5.00`).
- There are no tests. The proof command above is the only check.

Want me to apply this removal, or look at one of the passing issues instead?