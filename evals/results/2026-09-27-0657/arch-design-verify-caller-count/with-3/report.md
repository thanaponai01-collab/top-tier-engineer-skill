Yes, it's safe to remove `ShippingCalculator`, but it isn't unused. `FlatRateCalculator` subclasses it, so deleting `shipping/base.py` by itself breaks checkout and the nightly reprice job the moment they're imported. Two lines in `shipping/flat_rate.py` also have to change. Nothing else does.

**Why it looks unused but isn't (proven):**
- The only direct reference is `shipping/flat_rate.py:1` (the import) and `:4` (`class FlatRateCalculator(ShippingCalculator)`). There are no `isinstance`/`issubclass` checks, string lookups, type hints or docs that mention it.
- Both production callers still depend on it through the import chain `registry.py:1 → flat_rate.py:1 → base.py`. Those callers are `checkout/cart.py:5` and `jobs/reprice.py:6`.
- `jobs/reprice.py:2` imports `get_calculator as pick_calc`. A search for `get_calculator(` therefore misses the nightly job, which may be why it looked unused.
- On a scratch copy, deleting only `base.py` made both entry points fail with `ModuleNotFoundError: No module named 'shipping.base'`.

**What has to change:**
1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove line 1 (`from shipping.base import ShippingCalculator`) and change line 4 to `class FlatRateCalculator:`.
3. Leave `registry.py`, `cart.py` and `reprice.py` alone. The registry calls `quote(order)` on whatever class it holds and never checks the type.

On the scratch copy with those edits, both callers gave the same output as before (`15.0`, and shipping `5.0` on each repriced order), and no reference to `ShippingCalculator` was left.

**Is removing it the right call?** I'd say yes. The docstring says the class was kept "in case a second carrier is ever needed", but the thing that actually makes adding a carrier cheap is the `CALCULATORS` dict in `registry.py:3`. A second carrier is one new class with `quote()` plus one line in that dict, and it doesn't need a base class. If you later want the contract written down for a type checker, a `typing.Protocol` does that. Since it hasn't shipped, this is easy to undo: restore one 10-line file and one import.

**Caveats:**
- `fixture/` has no git history, requirements or tests. So the three likely future changes I measured against (remove the class, add a carrier, change the price) are my assumptions, and I couldn't look at how often these files change together.
- I can only see inside `fixture/`. If any code outside it imports `shipping.base`, that code would break, which is why removing it before it ships is the right time.
- A second agent that wasn't told my conclusion recounted the references and got the same result.

**Report:** `fixture/docs/arch-design-shipping.md`, with the verdict "messy in places", one finding, one decision and one move with its proof command. The skill's own check fails when run in place (exit 1): with no git repo, it resolves file paths from `docs/` and can't pin a commit. On a scratch copy with git initialised, it passes with 0 broken and 0 stale. I didn't change anything else in `fixture/`; the deletion itself is for you to do.

<!-- file written by the agent: fixture/docs/arch-design-shipping.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; nothing to pin, no change history to measure)
- question: is the ShippingCalculator interface in shipping/ unused and safe to delete before it ships, and what has to change?
- yardstick: delete ShippingCalculator (1 module: shipping, 2 files); add a second carrier (1 module: shipping, new file + shipping/registry.py:3); change the flat price (1 module: shipping/flat_rate.py:8)   (assumed: no requirements, issues or git log available)
- status: open
- verdict: messy in places
- context: callers keep going through shipping.registry.get_calculator; the registry and the `quote(order)` method name do not change; nothing outside fixture/ imports shipping.base (unverifiable here: not yet shipped, per the request)

## Finding 1: ShippingCalculator is a one-implementation interface, but it is not unused
- where: shipping/base.py:8, shipping/flat_rate.py:1, shipping/flat_rate.py:4
- cost: 1 abstract class, 1 subclass, 0 isinstance/issubclass/string lookups; 2 production callers (checkout/cart.py:5, jobs/reprice.py:6) reach it transitively via shipping/registry.py:1 -> shipping/flat_rate.py:1 -> shipping/base.py
- badge: strong
- evidence: proven — grep for ShippingCalculator|shipping.base|isinstance|issubclass|getattr|importlib finds only flat_rate.py:1,4; in a scratch copy, deleting base.py alone makes the checkout and nightly-reprice probe fail with ModuleNotFoundError: No module named 'shipping.base'
- note: "unused everywhere they checked" misses the subclass import; jobs/reprice.py:2 also imports get_calculator under an alias (pick_calc), so a grep for `get_calculator(` undercounts callers
- history: docstring shipping/base.py:3 records the reason ("a seam in case a second carrier is ever needed"); the seam callers actually use is the registry dict (shipping/registry.py:3), which works by duck typing on quote() and needs no base class

## Decision 1: remove the base class or keep it as the carrier seam
- options: delete shipping/base.py and drop the base from FlatRateCalculator | keep it (optionally as typing.Protocol) until a second carrier arrives
- forces: a second carrier needs only a new class with quote() plus a registry entry, so the base class buys nothing at runtime; its only payoff is documenting the contract, which a Protocol or the registry docstring can do if a type checker is ever added
- door: two-way, internal module not yet shipped; rollback is restoring one 10-line file and one import
- evidence: proven — scratch-copy run below gives identical output before and after

## Move 1: delete shipping/base.py and un-subclass FlatRateCalculator
- cost: 10-line abstract class plus 1 import line and 1 base-class reference kept alive for 1 implementation
- pays: delete-the-interface change: 2 files in shipping/ and 0 caller edits; add-a-carrier stays 1 new file + 1 registry line with no base to subclass
- files: shipping/base.py, shipping/flat_rate.py:1, shipping/flat_rate.py:4
- owner: shipping/registry.py (the CALCULATORS map is the seam; every calculator is any class with quote(order))
- callers: shipping/flat_rate.py:1 (delete `from shipping.base import ShippingCalculator` and the blank line after it), shipping/flat_rate.py:4 (`class FlatRateCalculator(ShippingCalculator):` -> `class FlatRateCalculator:`); no changes to shipping/registry.py, checkout/cart.py, jobs/reprice.py
- door: two-way, land it and go
- proof: from fixture/, run `python3 -c "import sys; sys.path.insert(0,'.'); from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{'subtotal':10.0},{'subtotal':0}]; r(o); print(t({'subtotal':10.0}), o)"` before and after; both must print `15.0 [{'subtotal': 10.0, 'shipping': 5.0}, {'subtotal': 0, 'shipping': 5.0}]`, and `grep -rn ShippingCalculator --include=*.py .` must print nothing
- effort: S
- after: nothing
