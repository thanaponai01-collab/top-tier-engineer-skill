I ran `latent-audit` over `fixture/` and found nothing that is proven safe to delete yet. The two modules nothing references are `app/services/legacy_export.py` and `app/models/notify.py`. Neither is imported, named in a string, or loaded at runtime. But I couldn't rule out outside callers, because the repo has no git history, CI config, cron file, packaging metadata or entry point. They go on the watch list until the owner confirms. I also found one real layer breach.

I swept all 12 modules in `fixture/` with the graph script, grep and a runtime tracer. `layers.txt` was written from `fixture/ARCHITECTURE.md` (routes > services > models). I changed nothing.

| Candidate | Finding | Checks: 1 refs · 2 outside callers · 3 runtime | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | Dead candidate | 1 ✅ no import, string or config reference anywhere · 2 ❌ couldn't check · 3 ✅ not loaded by the tracer | **Watch.** Its docstring says it was replaced by the plugins. If nobody external runs it, delete it in its own commit. Removing it saves 5 lines and one confusing "which export is real?" question. |
| `app/models/notify.py` (`subject`) | Dead candidate **and** the layer breach | 1 ✅ · 2 ❌ · 3 ✅ not loaded | **Watch.** If it's confirmed dead, deleting it also removes the breach. If it's live, fix the breach (below). |
| `app/plugins/csv_out.py` (`render`) | Script says "unused" | **Live** (traced + proven): `registry.py:4` names it in `ENABLED_PLUGINS`, and `registry.load()` loaded it in my run | **Keep.** This is exactly the plugin-registry case the architecture doc warns about. |
| `app/routes/web.py` `handle` | Script says "unused" | Nothing in-tree calls it, but it's the HTTP entry point. It is called from outside the repo by design | **Keep.** It's the top of the only real call chain: `handle → place_order → save`. |
| `fixture/app/models/notify.py:2` | **Layer breach (proven)** | The data layer imports `BANNER` from `app.routes.web` (interface). `ARCHITECTURE.md` says "never a higher one" | Pick one: delete `notify.py` if it's dead, or move `BANNER` down into models or config. Changing the architecture declaration doesn't make sense for a data→interface import. |

**What would unblock deletion:** confirm that no external job, service or person imports `app.services.legacy_export` or `app.models.notify`. Tell me who owns the deploy or cron setup, or say "confirmed unused", and I'll remove each in its own commit so either one can be reverted in one step. There's no git repo here yet, so I'd need to `git init` first for that.

**Evidence:**
- **Script:** `graph-audit.py fixture --layers layers.txt` found 12 modules, 3 import edges, 2 dead-module suspects, 4 unused-def suspects and 1 breach. It also listed 4 modules outside any declared layer (`registry`, `plugins/*`, `app/__init__`). The architecture doc doesn't place those, so they're not breaches.
- **Tracer:** I imported `registry` and `routes.web`, ran `registry.load()`, and called `handle({"items":[...]})`, which returned `1`. The loaded modules were `order`, `csv_out`, `registry`, `web` and `orders`. Neither `legacy_export` nor `notify` was loaded.
- **Bugs spotted on the way, not chased:**
  - `routes/web.py:8` raises a `KeyError` (so a 500, not a 400) on a payload without `"items"`. `services/orders.py:6` does the same for an item without `"price"`.
  - `models/order.py:2` keeps orders in a module-level list. They're lost on restart and not safe with multiple threads.