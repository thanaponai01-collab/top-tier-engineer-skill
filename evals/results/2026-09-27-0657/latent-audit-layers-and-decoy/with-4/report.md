**Nothing is safe to delete yet, but two modules are strong candidates:** `app/services/legacy_export.py` and `app/models/notify.py`. They pass two of the three checks. The third, confirming that nothing outside the repo calls them, can't be done from here. There's no git history, CI, cron or deploy config to look at, so they stay on the watch list until someone who knows the deployment confirms. Everything else is in use, including the plugin that looks dead. There is also one real layer breach.

Swept: all 12 Python modules in `fixture/`. The layer order comes from `fixture/ARCHITECTURE.md` ("1. `app/routes/` — interface … 3. `app/models/` — data"). Deleting both candidates would remove 2 of 5 real modules and would also clear the layer breach.

| Candidate | Verdict | Evidence | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | Watch (strong) | No import, string or config mentions `legacy_export` or `to_xml` (proven, grep). It never loaded in a run of the request path plus plugin loading (proven). Its docstring says plugins replaced it. **Not checked:** outside callers such as scripts or cron. | Delete in its own commit once the owner confirms no one runs it outside the repo. |
| `app/models/notify.py` (`subject`) | Watch (strong) | Same checks, same results: no in-tree references and never loaded (proven). **Not checked:** outside callers. | Same. Deleting it also removes the layer breach. |
| `app/plugins/csv_out.py` (`render`) | **Keep** | The script flags it as unused, but that's wrong. `app/registry.py:4` names it in `ENABLED_PLUGINS`, `importlib` loads it at `registry.py:8`, and the run loaded it and called `render` (proven). `ARCHITECTURE.md` documents this pattern. | None. |
| `app/routes/web.py:7` `handle` | Keep (suspected entry point) | Nothing in the repo calls it. It's the HTTP handler, so a web framework or server outside the repo presumably calls it. | None. |
| `app/registry.py:7` `load` | Keep (suspected entry point) | Nothing in the repo calls it either, and there's no app bootstrap here. Presumably whatever starts the app calls it. | None. Worth asking where the app actually starts. |
| `app/models/notify.py:2` | **Breach** (proven) | The data layer imports `BANNER` from the interface layer (`app.routes.web`). This makes the storage layer depend on HTTP code. | Delete `notify.py` (preferred, since it's unused), or move `BANNER` down into models or a constants module. Changing the documented layer order isn't a sensible fix here. |

**Notes:**
- `app/registry.py` and `app/plugins/` don't belong to any declared layer, so layer checks don't cover them. That's a gap in the architecture doc, not a breach.
- The runtime check ran `web.handle(...)` and `registry.load()` and then listed every loaded module. Everything except `legacy_export` and `notify` loaded.
- Bug noticed in passing, not chased: `services/orders.py:6` raises a `KeyError` if an item has no `price`. And `models/order.py:2` keeps orders in an in-memory list, so they're lost on restart. That may be deliberate for a fixture.

I haven't changed any files. If you confirm nothing outside the repo uses those two modules, I can remove them, one per commit, with the evidence in each commit message. The directory isn't a git repo yet, so I'd need to run `git init` first to make those commits.