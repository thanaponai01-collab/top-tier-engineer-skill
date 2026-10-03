**Verdict:** `ShippingCalculator` in `shipping/base.py` can be deleted. It isn't unused, though. `shipping/flat_rate.py` subclasses it, so deleting the file alone breaks that import. The removal is a two-way door (an internal class, nothing published), and I found no recorded reason to keep it.

**What has to change** (*traced*: I read all 5 files in `fixture/`, and a grep for the name and its imports found nothing else):
1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py:1,4`, remove `from shipping.base import ShippingCalculator` and change the class line to `class FlatRateCalculator:`.
3. Nothing else changes.
   - `checkout/cart.py:1` and `jobs/reprice.py:2` import only `get_calculator` from `shipping/registry.py`. `reprice.py` renames it to `pick_calc`, which is probably why a name search missed it.
   - Both call `.quote(order)` on whatever the registry returns, so they never touch the base class.
   - `registry.py` imports `FlatRateCalculator` directly and never mentions the base class.

**Why removing it is fine:**
- It has exactly one implementer, `FlatRateCalculator`, which returns a constant `5.00`. The class's own docstring says it exists "in case a second carrier is ever needed".
- The real seam is `registry.CALCULATORS` (`registry.py:3`), which maps a name to a class. It stays, so adding a carrier later still means one new class and one dict entry.
- What you lose is a declared contract (`quote(order)`) and the `NotImplementedError` guard. Add a `Protocol` or base class back when a second carrier exists.

**Not checked:**
- **Git history:** the directory isn't a git repo, so there's no `git log -S` for the symbol. "No recorded reason" here means only that the docstring is the sole stated reason.
- **Other code:** there are no tests or other repos in the fixture. If anything outside `fixture/` imports `shipping.base` or subclasses the class, it would break. Grep those before merging.
- **Tooling:** I skipped the import-graph and change-history scripts. With 5 files and 4 import edges, reading them was more reliable.
- **Output:** I made no edits and wrote no `docs/arch-design.md`, since this is a single decision with a small move.

**Decision row:**
- options: delete the base class and inline it into `FlatRateCalculator` | keep it as a one-implementer seam
- forces: a seam with one implementer is a guess; the registry already gives the extension point; the cost of being wrong is re-adding a 3-line class
- door: two-way
- evidence: traced