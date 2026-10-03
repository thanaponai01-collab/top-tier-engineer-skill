**Verdict: safe to remove, but not by deleting the file alone.** Deleting `shipping/base.py` on its own breaks checkout and the nightly job at import time. I ran that and got `ModuleNotFoundError: No module named 'shipping.base'` from `import checkout.cart` (*proven*).

**Why it looked unused:** callers never name `ShippingCalculator`. They go through `get_calculator("flat")`, and `jobs/reprice.py:2` renames that to `pick_calc`, so a grep for `get_calculator` misses it. The interface is still used in one place, as the parent class of `FlatRateCalculator` (`shipping/flat_rate.py:1` and `:4`). A grep for its name across `fixture/` shows only `base.py:8` and `flat_rate.py:1,4`, and nothing uses `importlib` or `getattr` (*proven*).

**What has to change** (two files, nothing else):
1. `shipping/flat_rate.py`: drop line 1 (the import) and change line 4 to `class FlatRateCalculator:`.
2. Delete `shipping/base.py`.

`registry.py`, `checkout/cart.py` and `jobs/reprice.py` don't change. They only call `.quote(order)`, so they don't depend on the base class.

**Why removing it is right (deletion test):**
- It has one implementer, and its own docstring says so: "in case a second carrier is ever needed."
- `.quote()` is duck-typed, so the base class enforces nothing. Its only behavior is `raise NotImplementedError`.
- Removing it leaves a smaller system, so this is a real finding. I'd rate it *worth exploring* rather than strong, since the cost is small and only pays off if a second carrier never arrives.
- It is a two-way door. Re-adding the interface later is a few lines, so no confirmation is needed.

**Before you merge:**
- **Callers outside `fixture/`:** I only checked this directory. Any repo that imports `shipping.base` from outside it would break, and I didn't check for those (*suspected*).
- **No tests or history:** there are no tests and no git history here, so I can't say why the seam was added. The only recorded reason is that docstring.
- **After the edit:** rerun the smoke check I used (`total_with_shipping({'subtotal':10})` returned 15.0, and `reprice_open_orders` set `shipping` to 5.0). Both should give the same output.

I didn't write `docs/arch-design.md`, because this is a single two-file decision that fits in the chat. I didn't make the edit, since you asked whether it's safe and what would change.