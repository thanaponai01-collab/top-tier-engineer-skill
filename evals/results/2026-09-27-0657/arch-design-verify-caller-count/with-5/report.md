**Yes, it's safe to delete.** The interface is `ShippingCalculator` in `shipping/base.py:8`. Removing it means changing one other file, `shipping/flat_rate.py`. No caller needs to change.

**What has to change:**
1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove the import on line 1 and change line 4 to `class FlatRateCalculator:`.

**Why it's safe:**
- **The interface does nothing at runtime.** Its only method raises `NotImplementedError`. It has one subclass, `FlatRateCalculator`. Nothing uses it in an `isinstance`/`issubclass` check, a type hint, a re-export or a string name. I grepped all 5 files, and a separate subagent recounted without being told what I expected; the counts matched.
- **The code that uses shipping never names the interface.** `checkout/cart.py:6` and `jobs/reprice.py:8` call `.quote()` on whatever `shipping/registry.py` returns.
- **Tested:** in a scratch copy I ran both entry points before and after the deletion. The output was identical: `total_with_shipping` gave `15.0`, and each repriced order got `shipping: 5.0`. The real `fixture/` code is untouched.
- **Easy to undo:** it's unreleased internal code, so restoring means re-adding a 10-line file and one base class.

**Where "looks unused" could have misled them:** `jobs/reprice.py:2` imports the registry lookup under another name: `get_calculator as pick_calc`. A search for `get_calculator(` misses the call at line 6. This doesn't affect deleting the interface, but anyone later changing `get_calculator` has to count that caller too.

**What you give up:** the file's docstring says it's kept as a hook in case a second carrier is needed. You don't need it for that. The registry dict in `registry.py:3` already lists carriers in one place, so a second carrier is a new class plus one registry entry.

The audit is written to `fixture/arch-design-shipping.md`: verdict "messy in places", 2 findings, 1 decision, 1 move with its proof command. I put it at the fixture root instead of `docs/` because the format check can only find the referenced files that way when there's no git repo. The check shows 0 broken fields but exits 1 with one warning: `fixture/` isn't a git repo, so the `at:` field has no commit to point to. I didn't run `git init` in your fixture. If you want a clean pass, initialise a repo and put the commit in `at:`.

<!-- file written by the agent: fixture/arch-design-shipping.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; analysis true of the tree on 2026-09-27)
- question: is ShippingCalculator (shipping/base.py) safe to delete before it ships, and what must change?
- yardstick: delete the unused interface (touches 2 files, 1 module: shipping); add a pricing rule to flat rate (1 file: shipping/flat_rate.py); add a second carrier (1 module: shipping, plus registry entry)
- context: shipping code is unreleased, so nothing outside fixture/ depends on it; registry.get_calculator and .quote(order) stay the call surface
- status: open
- verdict: messy in places

## Finding 1: ShippingCalculator is an interface with one implementation and no type-level users
- where: shipping/base.py:8
- cost: 1 implementation (shipping/flat_rate.py:4), 0 isinstance/issubclass/type-hint uses, 0 direct callers; 2 runtime callers of quote() reach FlatRateCalculator through the registry and never name the base (checkout/cart.py:6, jobs/reprice.py:8)
- badge: strong
- evidence: proven, grep over all 5 .py files for ShippingCalculator|isinstance|issubclass|getattr|import_module found only base.py:8 and flat_rate.py:1,4; in a scratch copy, removing base.py and the base class gave identical output from total_with_shipping and reprice_open_orders (15.0; shipping=5.0 on each order)

## Finding 2: a caller reaches the registry through an alias
- where: jobs/reprice.py:2
- cost: 1 of 2 call sites imports get_calculator as pick_calc, so a search for "get_calculator(" misses the call at jobs/reprice.py:6
- badge: worth exploring
- evidence: traced, read jobs/reprice.py in full. Doesn't block Move 1, which changes nothing callers import, but any later change to get_calculator must count this site

## Decision 1: delete the interface or keep it
- options: delete base.py and drop the base class (the base's docstring says it's a seam kept "in case a second carrier is ever needed") | keep it as that seam
- forces: no second carrier is in any requirement seen; callers already get duck typing through the registry, so a second carrier can be added later without the base; the base's only behavior is raising NotImplementedError
- door: two-way (internal, unreleased; restore is re-adding a 10-line file and one base class)
- evidence: proven, scratch-copy run above

## Move 1: remove ShippingCalculator
- cost: 1 file and 1 inheritance edge carrying no behavior (shipping/base.py:8-10)
- pays: add a second carrier: the new class has no abstract base to keep in step with; registry.CALCULATORS stays the one place carriers are listed
- files: shipping/base.py (delete), shipping/flat_rate.py:1 (remove import), shipping/flat_rate.py:4 (class FlatRateCalculator:)
- owner: shipping/registry.py stays the single owner of which calculators exist
- callers: none import ShippingCalculator except shipping/flat_rate.py:1,4; quote() callers checkout/cart.py:6 and jobs/reprice.py:8 (via pick_calc alias, :2,:6) need no change
- door: two-way, land it and go
- proof: from fixture/, `grep -rn ShippingCalculator --include=*.py .` prints nothing, and `python3 -c 'from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{"subtotal":10.0}]; r(o); print(t({"subtotal":10.0}), o)'` prints `15.0 [{'subtotal': 10.0, 'shipping': 5.0}]`
- effort: S
- after: nothing
