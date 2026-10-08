**Verdict: clean, with one speculative seam. Deleting `ShippingCalculator` is safe, but it isn't unused, so it takes a small edit. Only the unused-looking part is "no caller names it".**

**Outcome chosen:** Improve (a local change). You can override this.

**Why "looks unused" is misleading**
- `fixture/shipping/flat_rate.py:1` imports it, and `flat_rate.py:4` subclasses it: `class FlatRateCalculator(ShippingCalculator)`.
- Deleting `shipping/base.py` alone would break `flat_rate.py` with an ImportError. `registry.py` imports `flat_rate`, so `checkout/cart.py` and `jobs/reprice.py` would fail too.
- Callers never name the interface. `cart.py:1` and `reprice.py:2` only call `get_calculator("flat")`, and `reprice.py` aliases it as `pick_calc`. That is probably why a search for the name found nothing. Searching for it by name finds only the two hits in `flat_rate.py`.

**Is it safe? Yes, with evidence as follows**
- **Traced:** I read all 5 files in `fixture/`. The class has 1 implementer (`FlatRateCalculator`) and 0 other references. Its body is a single `raise NotImplementedError` (`base.py:8-10`).
- **Traced:** The only dynamic-lookup patterns I searched for (`importlib`, `getattr`, `__import__`) have 0 hits, so nothing loads it by string.
- **Not checked:** Code outside `fixture/`, such as other repos, plugins, or pickled or serialized references to `shipping.base.ShippingCalculator`. There's no git history here, so I can't see why it was added. The docstring (`base.py:3-4`) gives the reason: "in case a second carrier is ever needed". That is a guess, not a requirement. One implementer is a guess and two is a fact, so the deletion test passes: removing it leaves nothing behind.

**What has to change (2 files, behavior unchanged)**
1. `shipping/flat_rate.py`: remove line 1 and change line 4 to `class FlatRateCalculator:`. The `quote` method stays as is.
2. Delete `shipping/base.py`.

`registry.py`, `cart.py` and `reprice.py` need no change.

**Second option: keep it.**
- It costs about 6 lines and no runtime. It is cheap, but it implies a contract that nothing enforces. Python doesn't check it, and there is no ABC.
- Keep it only if a second carrier is a requirement you can name. If it is, make `quote` an `abc.abstractmethod` so the seam actually enforces something.
- The `CALCULATORS` dict in `registry.py:3` is the real extension point. A second carrier would work with duck typing, without the base class.

**Door:** two-way. This is an internal class with no stored data and no public API as far as I can see. Re-adding it later is a 6-line change.

**Proof**
- Before and after the edit, run `python -I -c "from checkout.cart import total_with_shipping as t; print(t({'subtotal': 10}))"` from `fixture/`. It should print `15.0` both times.
- Also run `python -I -c "import jobs.reprice"`.
- Then run `grep -r ShippingCalculator .`, which should return nothing.
- I haven't run these, and there are no tests in `fixture/`.

**Ranking:** this is the only move. It is tidying more than a saving, since it removes 1 file and 1 import, and nothing gets cheaper to change. Do it only if you agree that no second carrier is planned.