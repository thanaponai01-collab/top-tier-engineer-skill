Yes, it's safe to remove `ShippingCalculator` (`shipping/base.py:8`), but deleting the file alone breaks things. It isn't actually unused: `shipping/flat_rate.py` imports it and subclasses it. If only `base.py` goes, checkout and the nightly reprice job both fail with `ModuleNotFoundError: No module named 'shipping.base'`. I ran that in a scratch copy.

**What has to change** (3 edits, all in `shipping/`):
1. Delete `shipping/base.py`.
2. `shipping/flat_rate.py:1`: remove `from shipping.base import ShippingCalculator`.
3. `shipping/flat_rate.py:4`: change `class FlatRateCalculator(ShippingCalculator):` to `class FlatRateCalculator:`.

Nothing else changes. `checkout/cart.py:5` and `jobs/reprice.py:6` get their calculator from `shipping/registry.py` and just call `.quote(order)`, so they never refer to the base class.

**Evidence:**
- **Nothing else depends on it.** I searched `fixture/` for the class name, `shipping.base`, `isinstance`, `getattr`, `importlib` and `__subclasses__`. The only hits were `flat_rate.py:1` and `:4`. A separate subagent, which wasn't told what I expected, recounted and got the same two lines.
- **Behaviour is unchanged.** I made all three edits in a scratch copy. `total_with_shipping` still returns `15.0` and `reprice_open_orders` still sets shipping to `5.0`, the same as before.
- **It isn't needed for a second carrier.** Its docstring says it's kept "in case a second carrier is ever needed." The class checks nothing at runtime; its only body is `raise NotImplementedError`. New carriers get added in `registry.py:3`. Without the base class, adding one means editing 2 files instead of 3.
- **Easy to undo.** It hasn't shipped and nothing outside this tree imports `shipping/`. Putting it back means restoring 10 lines.

**Two cautions:**
- Don't take the same "unused" approach to `registry.get_calculator`. Both callers use it, and the nightly job imports it under an alias (`jobs/reprice.py:2`, `get_calculator as pick_calc`). A search for `get_calculator(` misses that call.
- The fixture has no git history, so I couldn't check whether anyone recorded a reason for the base class beyond its docstring.

The audit is written to `fixture/docs/arch-design-shipping.md`: two findings, one decision and one move, with the proof command. The file's checker only passes inside a git repo, so I ran it on a git-initialised copy, where it passed with 0 broken and 0 stale. Run against the plain fixture it fails, but only on path resolution and the unpinned commit. I didn't edit any source files in `fixture/`.

<!-- file written by the agent: fixture/docs/arch-design-shipping.md -->
# ARCH-DESIGN
- at: no-git (fixture has no history; analysis true of the tree on 2026-09-27)
- question: is shipping.base.ShippingCalculator safe to delete before it ships, and what must change?
- yardstick: add a second carrier (the one change base.py:3 names; 3 files in shipping/ today, 1 module); change the flat rate (1 file, 1 module); add a shipping caller (1 file + registry import, 2 modules)
- status: open
- verdict: messy in places
- context: callers keep reaching calculators via shipping.registry.get_calculator; the quote(order) duck-typed contract stays; shipping/ has no importers outside this tree

## Finding 1: ShippingCalculator is an interface with one implementation and no type-based users
- where: shipping/base.py:8
- cost: 10 lines, 1 implementation (shipping/flat_rate.py:4), 0 isinstance/type/dynamic uses, 0 imports outside shipping/flat_rate.py:1; its only body is `raise NotImplementedError`
- badge: strong
- evidence: proven, grep across fixture/ for ShippingCalculator, shipping.base, isinstance, getattr, import_module, __subclasses__ found only base.py:8 and flat_rate.py:1,4; deletion rehearsed in a copy and both call paths ran unchanged; independent subagent recount agreed (only flat_rate.py:1,4)

## Finding 2: it is not unreferenced; deleting base.py alone breaks checkout and the nightly job
- where: shipping/flat_rate.py:1
- cost: 1 import chain (flat_rate.py:1 -> registry.py:1 -> checkout/cart.py:1 and jobs/reprice.py:2); 2 entry points fail with ModuleNotFoundError
- badge: strong
- evidence: proven, deleted shipping/base.py in a scratch copy and ran total_with_shipping and reprice_open_orders: ModuleNotFoundError: No module named 'shipping.base'

## Decision 1: keep the base class as a seam, or delete it
- options: delete ShippingCalculator and rely on duck-typed quote(order) via the registry | keep it for a possible second carrier (base.py:3)
- forces: the only recorded reason is "in case a second carrier is ever needed" (base.py:3), with no requirement behind it; the base class enforces nothing at runtime, and the registry (registry.py:3) is the real extension point, so a second carrier costs the same with or without it; one caller-less abstraction under 100 lines should be inlined
- door: two-way, it is unreleased and internal; restoring it is re-adding 10 lines and one base-class reference
- evidence: proven, rehearsal in a scratch copy produced the same outputs (15.0 and shipping 5.0) before and after

## Move 1: delete ShippingCalculator and detach FlatRateCalculator from it
- cost: 10-line file plus 1 import and 1 base-class reference that add no behaviour
- pays: add a second carrier: 3 files (base, new class, registry) -> 2 (new class, registry)
- files: shipping/base.py:1-10 (delete file); shipping/flat_rate.py:1 (remove import); shipping/flat_rate.py:4 (`class FlatRateCalculator(ShippingCalculator):` -> `class FlatRateCalculator:`)
- owner: shipping/registry.py owns which calculators exist; the contract is quote(order) -> number
- callers: shipping/flat_rate.py:1, shipping/flat_rate.py:4 (the only references); checkout/cart.py:5 and jobs/reprice.py:6 (aliased as pick_calc) need no edit
- door: two-way, land it and go
- proof: from fixture/, `grep -rn ShippingCalculator .` prints nothing, and `python3 -c 'import sys; sys.path.insert(0,"."); from checkout.cart import total_with_shipping; from jobs.reprice import reprice_open_orders; o=[{"subtotal":10}]; print(total_with_shipping(o[0])); reprice_open_orders(o); print(o)'` prints `15.0` then `[{'subtotal': 10, 'shipping': 5.0}]`
- effort: S
- after: nothing
