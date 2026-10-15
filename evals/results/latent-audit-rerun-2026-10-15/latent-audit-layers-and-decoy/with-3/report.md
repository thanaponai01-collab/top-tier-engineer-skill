I ran latent-audit over `fixture/` and nothing is safe to delete yet. Two modules are very likely dead, but nobody can rule out callers outside the repo, so both stay on a watch list. I deleted nothing.

**What I swept:** all 12 Python modules, the import graph, every name referenced in strings, and `ARCHITECTURE.md`. The repo has no git history, tests, CI, cron or deploy config, and no entry point (no `main` or server wiring). To trace at runtime I treated `routes.web.handle` and `registry.load()` as the entry points and ran both.

**Layer order** is declared at `ARCHITECTURE.md:5-7`: routes (interface) above services (domain) above models (data). `app/plugins/` and `app/registry.py` sit outside that order, which is a gap in the declaration rather than a breach.

| Candidate | Finding | Proof / unfinished check | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | dead (suspected) | 1. No import, no string reference, no registry entry. 3. Not loaded in the runtime trace. **2. Outside callers not checked:** someone may run it as a script or call it from another service. Its docstring says the plugins replaced it. | **Watch.** Delete once the owner confirms nothing outside the repo calls it. Gain: about 5 lines. |
| `app/models/notify.py` (`subject`) | dead (suspected) **and a layer breach** | 1. Nothing imports it or names it. 3. Not loaded in the trace. **2. Outside callers not checked.** | **Watch.** Deleting it would also remove the only layer breach. |
| `app/models/notify.py:2` → `app.routes.web.BANNER` | breach (proven) | A real import: the data layer pulls in the interface layer, and with it services and the order model. | Either delete `notify.py`, or move `BANNER` into models or a shared constants module. The other option is changing the architecture doc, which isn't warranted here. |
| `app/plugins/csv_out.py` (`render`) | **live, keep** | Only a string reaches it: `registry.py:4` lists `"app.plugins.csv_out"` in `ENABLED_PLUGINS`. The trace confirmed it loads and renders. | Keep. This is the trap: no import mentions it, but it is in use. |
| `app/routes/web.py` `handle` | live, keep | Nothing in the repo calls it. It is the HTTP interface named in `ARCHITECTURE.md:5`, so its caller is outside the repo. It runs correctly. | Keep. |

The script flagged 6 suspects (2 modules, 4 functions). I checked all 6; none were left unchecked.

**What would move the two watch items to the delete list:** confirmation from someone who knows the deployment that no cron job, other service or person invokes `legacy_export` or `notify`. With that, each one goes in its own commit.

**Bugs I passed, not chased:**
- `registry.py:8`: if any entry in `ENABLED_PLUGINS` fails to import, `load()` raises and none of the plugins load.
- `routes/web.py:8`: a payload without `"items"`, or an item without `"price"` (`services/orders.py:6`), raises an unhandled `KeyError`, which would surface as a 500 error.
- `models/order.py:2`: storage is a module-level list. It isn't thread-safe and is lost on restart.

**Runs:**
- **Graph script:** 12 modules, 3 import edges. It reported `dead: 2, unused: 4, layer-breaches: 1` and labelled every dead and unused item as a suspect. It had to run without Python's `-I` isolation flag, because that flag hides the script's own helper module.
- **Tracer:** loaded `app.models.order`, `app.plugins.csv_out`, `app.registry`, `app.routes.web` and `app.services.orders`, plus the package `__init__` files. It never loaded `legacy_export` or `notify`.

The layers file and tracer script are in `%TEMP%\tte-audit-work\`, outside the repo.