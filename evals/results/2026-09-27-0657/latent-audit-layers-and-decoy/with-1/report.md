I can't say anything in `fixture/` is safe to delete yet, but one file is close: `app/services/legacy_export.py`. Nothing in the repo reaches it, and a test run never loaded it. The one check I couldn't do is whether anything outside the repo calls it (a script, a cron job, another service). The repo has no git history, CI, deploy config or tests to answer that, so only its owner can confirm it's unused.

I swept all 12 modules (8 with code, 4 empty `__init__.py` files) and changed nothing. The layer order comes from `ARCHITECTURE.md` ("routes → services → models, never import a higher layer").

| Candidate | Verdict | Checks: references / outside callers / test run | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | **watch**: strongest candidate | Nothing in the repo refers to it (checked imports, strings, config, docs) / **not checkable** / not loaded | Ask whoever ran the old XML export. If no one uses it, delete it in its own commit. Its docstring says the plugins replaced it. |
| `app/models/notify.py` (`subject`) | **watch** + **layer breach** | Nothing in the repo refers to it / **not checkable** / not loaded | See the breach below. If no one sends notifications, delete it and the breach goes with it. If they do, move `BANNER` down a layer. |
| `app/plugins/csv_out.py` (`render`) | **keep: live** | `registry.py:4` lists it in `ENABLED_PLUGINS` and loads it by name at runtime | Don't delete. The graph script flags `render` as unused, but that's wrong: no code imports the plugin, the registry loads it by name. |
| `routes/web.py:handle`, `registry.py:load` | **keep: entry points** | Nothing in the repo calls them because an outside server or runner calls them | Don't delete. |

**Layer breach (proven):** `app/models/notify.py:2` does `from app.routes.web import BANNER`. That's the data layer importing from the interface layer, which ties the storage code to the HTTP code just for a string constant. There are two fixes, and it's the owner's call:
- **Fix the code:** move `BANNER` into `models/` or a shared constants module.
- **Change the declaration:** allow the import in `ARCHITECTURE.md`. I don't recommend this, because the doc is explicit.

Deleting both files would remove 11 lines (2 modules) and the only layer breach. Beyond that, the codebase is already small and nearly all of it is used.

**How I know**
- **Graph (measured):** the bundled `graph-audit.py` script found 12 modules, 3 imports between them and 1 breach. It flagged `notify` and `legacy_export` as possibly dead, and `handle`, `render`, `subject` and `to_xml` as possibly unused. That list is a starting point, not proof.
- **Test run (proven):** calling `web.handle(...)` and `registry.load()` loaded `routes.web`, `services.orders`, `models.order`, `registry` and `plugins.csv_out`, and never `legacy_export` or `notify`. Other entry points I don't know about could still load them.
- **Layers:** `app/registry.py` and `app/plugins/` aren't in any declared layer, so no layer rules were checked for them. That's a gap in the architecture doc, not a breach.
- **Bugs noticed along the way:** `services/orders.py:6` raises a `KeyError` on any item without `"price"`, and `models/order.py:2` keeps orders in a module-level list, so they're shared across requests and never saved to disk. That list may just be a placeholder.

If you confirm nothing outside the repo uses the two files, I can delete them, one commit per file.