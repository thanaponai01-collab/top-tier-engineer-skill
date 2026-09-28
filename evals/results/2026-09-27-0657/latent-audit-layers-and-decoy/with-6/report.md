**Nothing is proven safe to delete yet.** Two modules, `app/services/legacy_export.py` and `app/models/notify.py`, are very likely dead. Each passed two of the three checks. The one I couldn't do is outside callers: this directory has no git history, deploy config, cron, CI or tests, so I can't rule out a script or another service loading them by name. Both are 5–6 lines, so deleting them saves almost nothing in size. The real gain is that removing `notify.py` also removes the repo's only layer breach.

Scope: all 12 Python modules in `fixture/`. The layer order comes from `fixture/ARCHITECTURE.md`: "1. `app/routes/` — interface … 2. `app/services/` — domain … 3. `app/models/` — data".

| Candidate | Finding | Evidence | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | watch, likely dead | Search: no import, string, config or registry entry mentions it. Its own docstring says "Superseded by the plugins". Run: it never loaded from the entry points I ran. **Not done:** outside callers | Confirm with the owner that no external script or job imports it, then delete in its own commit |
| `app/models/notify.py` (`subject`) | watch, likely dead, **plus layer breach** | Same search and run results as above. **Not done:** outside callers | Same as above. Deleting it also clears the breach |
| Breach at `app/models/notify.py:2` | layer breach (**proven**) | `from app.routes.web import BANNER`: the data layer imports from the interface layer to get a copy string | If you keep the file, move `BANNER` down to `models` (or pass it in). The alternative is changing the declared layers, which I wouldn't do for one string |
| `app/plugins/csv_out.py` (`render`) | **keep** | The script listed it as unused, but `app/registry.py:4` loads it by name through `ENABLED_PLUGINS` / `importlib`. It loaded in the run | Keep. The script was wrong because it can't see name-based loading |
| `app/routes/web.py` `handle` | **keep** | It's the HTTP entry point. The script flags it only because nothing in this repo calls it; the web framework does | Keep |

**Caveats:**
- The run gives weaker evidence than it sounds. Nothing in the repo says where the app starts (no main, server or test), so I picked `routes.web.handle()` and `registry.load()` as the likely entry points and ran them. Neither candidate module loaded. The runtime is *proven* for those two entry points, but the entry points themselves are my assumption.
- The first script run reported "layers unchecked". I wrote a layers file from ARCHITECTURE.md and reran it; that second run found the breach above.
- `app/plugins/`, `app/registry.py` and `app/__init__.py` aren't in any declared layer. That's a gap in the architecture doc, not a breach.

**Bugs noted in passing:** `app/models/order.py:2` keeps orders in a module-level list, so data is lost on restart and it isn't thread-safe. That may be intentional for a stub.

**Next step:** ask whoever runs this in production whether anything outside the repo imports `legacy_export` or `notify`. If nothing does, I can delete each in its own commit so either one can be reverted separately. I haven't changed any files.