**Short answer: nothing is proven safe to delete yet.** Two modules are strong candidates, `app/services/legacy_export.py` and `app/models/notify.py`. I couldn't finish the check for outside callers, so both go on a watch list for now. If you tell me no external system or person uses them, both can be deleted, one per commit. Everything else is in use, including the plugin, which only looks dead.

**Swept:** all 12 Python files in `fixture/app/` (about 40 lines). The layer order comes from `fixture/ARCHITECTURE.md`: "Three layers. A module may import its own layer or a lower one, never a higher one." Routes are on top, then services, then models.

**What deleting would buy:** very little code (11 lines in total). The real gain is that removing `notify.py` also removes the repo's only layer breach.

| File / symbol | Verdict | Evidence | Proposed action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | **watch** (probably dead) | ✅ Check 1: no import or string anywhere mentions it. ✅ Check 3 (**proven**): running the app entry points and loading the plugins never loads it. ❌ Check 2: no git history, CI, cron or deploy config here, so outside callers are unknown. Its own docstring says it was superseded by the plugins. | Delete once you confirm no external script or job calls `to_xml`. |
| `app/models/notify.py` (`subject`) | **watch**, plus a **layer breach** (**proven**) | Same results: checks 1 and 3 pass, check 2 is unfinished. The breach is at `app/models/notify.py:2`: `from app.routes.web import BANNER`, so the data layer imports from the interface layer. | Your call: (a) if it's abandoned, delete it and the breach goes with it; (b) if it's unfinished notification work, keep it and move `BANNER` down into models or services (or pass it in as an argument). |
| `app/plugins/csv_out.py` (`render`) | **live** | The script flags it as unused, but `app/registry.py:4` names it in `ENABLED_PLUGINS` and loads it with `importlib`. **Proven**: `registry.load()` returns it and `render` runs. | Keep. This is the plugin trap `ARCHITECTURE.md` warns about. |
| `app/routes/web.py` (`handle`) | **live** | It's the HTTP handler, so its caller is outside the repo. **Proven**: it runs through `orders.place_order` into `order.save`. | Keep. |
| `services/orders.py`, `models/order.py`, `registry.py` | **live** | All loaded in the run. | Keep. |

**Caveats:**
- The repo has no `main`, server, tests or git. For the run I used `web.handle` and `registry.load` as entry points, based on the docs. If some other entry point exists, the result for check 3 could change.
- Four modules (`app/__init__`, `registry`, and the two plugin modules) aren't in any declared layer. That's a gap in the declaration, not a breach.

**Bug noted in passing (not chased):** `app/services/legacy_export.py:5` builds XML without escaping, so a row containing `<` or `&` produces broken or injected XML. This is another reason not to revive that module.

**Script output (measured):** 12 modules and 3 import edges. It reported 1 layer breach, 2 suspected dead modules, and 4 suspected unused functions. The checks above sort all of them.

I haven't changed anything. If you confirm the two watch items have no outside callers, I'll remove each in its own commit so either one can be reverted in a single step.