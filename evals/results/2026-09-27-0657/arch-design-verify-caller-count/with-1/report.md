Yes, it's safe to remove. The interface is `ShippingCalculator` in `shipping/base.py:8`. The only thing that has to change is `shipping/flat_rate.py`: drop the import on line 1 and the base class on line 4. The two places that actually get shipping prices, `checkout/cart.py` and `jobs/reprice.py`, need no change. I tested this by running both of them before and after the removal.

**Verdict: messy in places.** This is an abstract class with exactly one subclass and nothing that uses it directly. Removing it is the one change worth making here.

**How I know:**
- **Every reference, found by search:**
  - The class is named only at `shipping/flat_rate.py:1`, where it's imported, and `:4`, where `FlatRateCalculator` inherits from it.
  - Nothing checks for it by type or loads it by name.
  - Both price calls, `checkout/cart.py:6` and `jobs/reprice.py:8`, get a `FlatRateCalculator` from `shipping/registry.py:7`. That class defines its own `quote()`, so the base class's `quote()` is never called.
- **Tested:** I made the change in a scratch copy and ran both callers. The output was identical before and after (`15.0`, shipping `5.0`), and no references to the class were left. Your `fixture/` is untouched apart from the new report file (see the last bullet).
- **Checked independently:** a separate agent recounted the references without being told what I expected, and got the same counts.

**One thing to know first:** `jobs/reprice.py:2` imports the lookup function as `get_calculator as pick_calc`. A search for `get_calculator(` misses that caller. That doesn't matter for deleting the interface, because neither caller uses it. It would matter if someone changes `shipping/registry.py` next.

**The reason it exists:** the docstring at `shipping/base.py:3` says it's kept "in case a second carrier is ever needed." That's the only reason recorded anywhere; there's no git history to check. It isn't a current requirement, and `shipping/registry.py` already lets you add a second carrier without it. Since nothing has shipped yet, nobody outside the code can be relying on it. Restoring it later means putting back a 10-line file.

**Written to:** `fixture/docs/arch-design-shipping.md`, with one finding, one decision and one move. The move lists the exact lines to change and the command that confirms it worked.

**The skill's file check (`arch-design.py check`) still fails, for two reasons that come from the missing git repo, not from the report:**
- Without git, it looks for file paths relative to `docs/`, so it reports every path as missing. When I ran it with `fixture/` as the base folder, all paths were found.
- It still flags the `at:` field as stale, because there's no commit to point to. That clears once `fixture/` is a git repo with a commit.

I didn't set up git in your folder without asking. I also skipped the before-and-after diagram, since the change is one small edit.

<!-- file written by the agent: fixture/docs/arch-design-shipping.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a repository; analysis true of the tree on 2026-09-27)
- question: shipping/base.py ShippingCalculator looks unused; is it safe to remove before it ships, and what has to change?
- yardstick: remove the ShippingCalculator seam (1 module: shipping); add a second carrier (shipping + registry, 1 module); change the flat rate (1 file)
- status: open
- verdict: messy in places
- context: FlatRateCalculator stays the only carrier; registry.get_calculator and its two callers keep their signatures

## Finding 1: ShippingCalculator is an interface with one implementation and no callers of its own
- where: shipping/base.py:8
- cost: 1 subclass (shipping/flat_rate.py:4), 1 import (shipping/flat_rate.py:1), 0 isinstance/issubclass/dynamic uses, 0 direct callers; both quote() call sites (checkout/cart.py:6, jobs/reprice.py:8) receive a FlatRateCalculator from shipping/registry.py:7
- badge: strong
- evidence: proven, grep over the tree plus both callers run before and after the removal in a scratch copy (15.0 / shipping 5.0 both times); subagent recount agreed on all counts

## Finding 2: the registry's second caller is behind an alias
- where: jobs/reprice.py:2
- cost: 1 of 2 registry callers imports get_calculator as pick_calc, so a search for "get_calculator(" misses it
- badge: worth exploring
- evidence: traced, jobs/reprice.py:2 and jobs/reprice.py:6 read; relevant if anyone later touches registry.get_calculator rather than base.py

## Decision 1: delete the seam or keep it
- options: delete shipping/base.py and the base class on FlatRateCalculator | keep it as the documented seam for a second carrier
- forces: the only recorded reason is the docstring at shipping/base.py:3 ("in case a second carrier is ever needed"), which is not a current requirement; Python duck typing means registry.py already works as the seam, so a second carrier can be added without the base class; nothing has shipped, so there are no external subclassers yet
- door: two-way, internal class that has not shipped; git or a 10-line file brings it back
- evidence: proven, removal applied in a scratch copy and both callers ran with identical output

## Move 1: Delete ShippingCalculator and un-subclass FlatRateCalculator
- cost: 10-line abstract class with 1 subclass and 0 direct uses (shipping/base.py:8)
- pays: remove the seam: 2 files in shipping/, 0 files outside it; checkout/cart.py and jobs/reprice.py are unchanged
- files: shipping/base.py:8 (delete the file); shipping/flat_rate.py:1 (drop the import); shipping/flat_rate.py:4 (class FlatRateCalculator: without a base)
- owner: shipping/registry.py stays the one place that maps a carrier name to a calculator
- callers: shipping/flat_rate.py:1, shipping/flat_rate.py:4 are the only references; checkout/cart.py:6 and jobs/reprice.py:8 call quote() on FlatRateCalculator and need no change
- door: two-way, land it and go
- proof: from fixture/, run: python3 -c "import sys; sys.path.insert(0,'.'); from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{'subtotal':10}]; r(o); print(t({'subtotal':10}), o)" and expect 15.0 [{'subtotal': 10, 'shipping': 5.0}]; then grep -rn "ShippingCalculator\|shipping.base" . --include=*.py should print nothing
- effort: S
- after: nothing
