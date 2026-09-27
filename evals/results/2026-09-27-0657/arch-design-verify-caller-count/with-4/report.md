Yes, it's safe to remove `ShippingCalculator` (`shipping/base.py:8`), but it isn't unused. Deleting only `base.py` breaks both checkout and the nightly reprice job. You also have to edit two lines in `shipping/flat_rate.py`.

**What has to change** (I ran this in a scratch copy):
1. Delete `shipping/base.py`.
2. `shipping/flat_rate.py:1`: remove `from shipping.base import ShippingCalculator`.
3. `shipping/flat_rate.py:4`: change `class FlatRateCalculator(ShippingCalculator):` to `class FlatRateCalculator:`.

Nothing else needs to change. `checkout/cart.py` and `jobs/reprice.py` only reach the class through `registry.get_calculator`, which checks nothing about the base class.

**Why it looks unused but isn't:**
- **Nobody calls it, but one class inherits from it.** `FlatRateCalculator` subclasses it and imports `shipping.base`. `registry.py:1` imports `flat_rate`, so if `base.py` alone disappears the import fails with `ModuleNotFoundError: No module named 'shipping.base'`. Both callers then fail with it.
- **It does nothing.** It's a `quote()` stub that raises `NotImplementedError`. There's only one implementation and no `isinstance` checks. Its docstring says it exists "in case a second carrier is ever needed", but adding a carrier today only takes a new class with `quote()` plus a line in `registry.py:3`. The base class doesn't make that easier.

**Evidence:**
- **Before and after:** both callers return `cart 15.0 job 5.0` before the change and after the 3-step change.
- **Naive deletion:** deleting only `base.py` fails with the error above.
- **Reference count:** grep, and a separate agent that wasn't told my conclusion, both found exactly two references, both in `flat_rate.py`.
- **History:** the fixture has no git history, so I couldn't check whether a second carrier was ever planned. The docstring is the only recorded reason.

**A trap if they go further and delete the registry:** `jobs/reprice.py:2` imports `get_calculator as pick_calc`, so searching for `get_calculator(` misses that caller. The move above keeps the registry, so it doesn't matter yet.

**Verdict:** messy in places. The change is small (effort S) and easy to undo, since nothing outside `shipping/` depends on the base class and it hasn't shipped. The move, its proof command and the full evidence are in `fixture/docs/arch-design-shipping.md`.

The skill's `check` script exits 0 on that file, but only in a scratch copy where I ran `git init` and set `at:` to that copy's commit. `fixture/` isn't a git repo, so there the check reports the file paths as missing and the `at:` line as stale. I didn't run `git init` in your directory.

<!-- file written by the agent: fixture/docs/arch-design-shipping.md -->
# ARCH-DESIGN
- at: no-git (fixture has no history; analysis is of the working tree on 2026-09-27)
- question: is the unused-looking interface shipping/base.py ShippingCalculator safe to delete before it ships, and what has to change?
- yardstick: change flat-rate pricing (1 module: shipping/flat_rate.py); add a second carrier (1 module: shipping/, new file + registry.py:3); delete the ShippingCalculator seam (1 module: shipping/, base.py + flat_rate.py:1,4)
- status: open
- verdict: messy in places
- context: registry.get_calculator and its two callers stay as they are; only the ShippingCalculator base class is removed

## Finding 1: ShippingCalculator is a one-implementation seam, and it is not unused
- where: shipping/base.py:8
- cost: 1 subclass (shipping/flat_rate.py:4), 1 import (shipping/flat_rate.py:1), 0 other references, 0 isinstance/issubclass checks; it adds only a quote() stub that raises NotImplementedError (base.py:9-10)
- badge: strong
- evidence: proven. grep for ShippingCalculator and shipping.base, plus a separate recount by a subagent that was not told the conclusion: both found 2 references, both in flat_rate.py. Deleting only base.py fails with ModuleNotFoundError: No module named 'shipping.base', and because registry.py:1 imports flat_rate, both callers (checkout/cart.py:5 and jobs/reprice.py:6) break too. Deleting it and editing flat_rate.py keeps the outputs the same (cart 15.0, job 5.0). The recorded reason (base.py:3-4 docstring, "in case a second carrier is ever needed") names a need that no code has today. There is no git history to check for more.

## Finding 2: one registry caller is hidden behind an import alias
- where: jobs/reprice.py:2
- cost: 2 call sites of get_calculator. One of them is called as pick_calc("flat") (reprice.py:6), so a grep for "get_calculator(" misses it.
- badge: worth exploring
- evidence: proven. grep and the subagent's recount both found it. It matters only if someone later removes or renames the registry: the registry is not what this move deletes.

## Decision 1: remove the seam or keep it
- options: delete base.py and make FlatRateCalculator a plain class | keep base.py as the documented extension point for a second carrier
- forces: no second carrier exists or is planned in the code (registry.py:3 has one entry); callers already duck-type through registry.get_calculator, so a new carrier needs only a class with quote() plus a registry entry, and the base class adds nothing to that; it has one caller and fewer than ~100 lines, which the bar says to inline
- door: two-way. base.py is internal to shipping/, nothing outside shipping/ imports it, and it has not shipped. Restoring it is one file plus one line.
- evidence: proven. It was run in a scratch copy, and both callers returned the same values before and after.

## Move 1: delete shipping/base.py and drop the base class from FlatRateCalculator
- cost: 10-line file with 1 subclass and no behavior (base.py:8-10)
- pays: add a second carrier: stays at 1 module (shipping/), with no stub base class to keep in sync; delete-seam yardstick: done
- files: shipping/base.py (delete); shipping/flat_rate.py:1 (remove `from shipping.base import ShippingCalculator`); shipping/flat_rate.py:4 (`class FlatRateCalculator(ShippingCalculator):` becomes `class FlatRateCalculator:`)
- owner: shipping/flat_rate.py FlatRateCalculator owns the quote contract; shipping/registry.py stays the only way in
- callers: shipping/flat_rate.py:1 and :4 are the only references. checkout/cart.py:5 and jobs/reprice.py:6 (alias pick_calc) reach it through registry.py and need no change.
- door: two-way, land it and go
- proof: run from fixture/: `python3 -B -c 'from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{"subtotal":10}]; r(o); print("cart", t({"subtotal":10}), "job", o[0]["shipping"])'` prints `cart 15.0 job 5.0`; then `grep -rn "ShippingCalculator\|shipping.base" --include=*.py .` prints nothing
- effort: S
- after: nothing
