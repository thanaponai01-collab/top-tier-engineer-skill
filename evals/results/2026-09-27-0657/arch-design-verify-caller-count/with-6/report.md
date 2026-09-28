Yes, `ShippingCalculator` in `shipping/base.py` is safe to delete. It takes two edits to one file plus deleting `base.py` itself. But it isn't really unused: it has exactly one subclass, so it's an over-built seam, not dead code. And the registry next to it (`get_calculator`) is in live use and must stay.

**What has to change** (I tested this on a scratch copy of the code):
1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove the `from shipping.base import ShippingCalculator` import on line 1.
3. In the same file, change line 4 to `class FlatRateCalculator:` so it no longer inherits from the base class.

Nothing else references it. There are no `isinstance`/`issubclass` checks, no dynamic lookups, no tests and no config. `checkout/cart.py` and `jobs/reprice.py` never touch the base class; they go through `shipping/registry.py`.

**Evidence**
- **Tested:** I ran both callers before and after the deletion. Output was identical: `total_with_shipping` returns `15.0` and the nightly reprice sets `shipping=5.0`. Afterwards, searching for `ShippingCalculator` finds nothing.
- **Independent recount:** a separate subagent, not told what I expected, counted references to each symbol. It found the same two references to the base class, both in `flat_rate.py`.
- **Why it exists:** the only recorded reason is its docstring, "in case a second carrier is ever needed" (`shipping/base.py:3`). There's no git history to check. That reason doesn't justify keeping it: the registry's `CALCULATORS` dict already works as the extension point, since any class with a `quote()` method can be added there. Putting a 3-line base class back later would take minutes. It's reversible.

**One trap if "the interface" means the registry rather than the base class:** `get_calculator` has two callers, and one is easy to miss. `jobs/reprice.py:2` imports it as `pick_calc`, so a search for `get_calculator(` misses the call at line 6. Deleting the registry would break the nightly reprice job.

**Audit verdict:** messy in places. This one-implementation base class is the only structural finding, and deleting it is the only proposed change.

The report is at `fixture/docs/arch-design-shipping.md`. The skill's `check` script needs a git repo and `fixture/` isn't one, so it fails in place. On a scratch copy with git set up it passed (exit 0: 0 broken, 0 stale). The `at:` field says `no-git` rather than a commit ID. I didn't make the change in the real `fixture/`.

<!-- file written by the agent: fixture/docs/arch-design-shipping.md -->
# ARCH-DESIGN
- at: no-git (fixture has no repository; snapshot of 2026-09-27)
- question: is the unused-looking interface in shipping/ safe to delete before it ships, and what must change?
- yardstick: remove the ShippingCalculator seam (2 modules: shipping/base.py, shipping/flat_rate.py); change the flat rate (1 module: shipping/flat_rate.py); add a second carrier (1-2 modules: shipping/ plus the caller that picks it)
- context: behavior of total_with_shipping and reprice_open_orders stays identical; the registry and get_calculator stay; nothing outside fixture/ imports shipping/
- status: open
- verdict: messy in places

## Finding 1: ShippingCalculator is a one-implementation seam with no callers
- where: shipping/base.py:8
- cost: 1 implementation (shipping/flat_rate.py:4), 0 type checks, 0 direct callers; every consumer goes through shipping/registry.py:6
- badge: strong
- evidence: proven, grep across fixture/ for the name, isinstance, issubclass, getattr, importlib finds only shipping/flat_rate.py:1 and :4; scratch copy with base.py removed gives identical output from both callers (15.0 and shipping=5.0); independent subagent recount agrees: 2 references, both in flat_rate.py

## Finding 2: the registry is NOT unused, one caller hides behind an alias
- where: jobs/reprice.py:2
- cost: 2 callers of get_calculator: checkout/cart.py:5 and jobs/reprice.py:6 (imported as pick_calc, so grepping for "get_calculator(" misses the call)
- badge: strong
- evidence: proven, grep for get_calculator and pick_calc across fixture/; independent subagent recount agrees: 2 call sites, one aliased

## Decision 1: delete the base class or keep it as a seam
- options: delete ShippingCalculator and drop the base from FlatRateCalculator | keep it for a future second carrier (its docstring's stated reason, shipping/base.py:3)
- forces: no second carrier in the requirements; a Python duck-typed registry already is the seam (any class with quote() can be added to CALCULATORS); re-adding a 3-line base class later costs minutes
- door: two-way, internal code, not yet shipped, no stored data or public API
- evidence: proven, scratch-copy run; no git history exists to consult, so the docstring is the only recorded reason

## Move 1: delete ShippingCalculator and un-inherit FlatRateCalculator
- cost: 1 file and 1 import that exist only to be subclassed once
- pays: remove the seam: 2 files touched, nothing else; add a second carrier stays 1-2 modules via CALCULATORS
- files: shipping/base.py:8 (delete file), shipping/flat_rate.py:1 (delete import), shipping/flat_rate.py:4 (class FlatRateCalculator: with no base)
- owner: shipping/registry.py:3 stays the one place that knows which calculators exist
- callers: shipping/flat_rate.py:1, shipping/flat_rate.py:4 (the only references); checkout/cart.py:5 and jobs/reprice.py:6 unchanged
- door: two-way, land it and go
- proof: `cd fixture && python3 -c 'from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{"subtotal":10}]; r(o); print(t({"subtotal":10}), o)'` prints `15.0 [{'subtotal': 10, 'shipping': 5.0}]` before and after, and `grep -rn ShippingCalculator .` prints nothing
- effort: S
- after: nothing
