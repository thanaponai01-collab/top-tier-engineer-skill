# Latent audit: `fixture/`

**Nothing is proven safe to delete yet.** There are two strong candidates, `app/services/legacy_export.py` and `app/models/notify.py`. Each passed two of the three checks. The one left is outside callers, and I can't check that from here: there's no git history, CI, cron or deploy config in the repo. Deleting both removes 11 of the ~35 source lines and the codebase's only layer violation. The script also flagged `render` and `handle` as unused, but they are live. Deleting them would break the app.

I swept all 12 modules in `fixture/`. Layers were checked against `ARCHITECTURE.md:3-7` ("routes → services → models; a module may import its own layer or a lower one, never a higher one").

| Candidate | Verdict | Proof / unfinished check | Action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | **watch**, strong candidate | ① No import, string, config or registry entry names it (*traced*, grep across the whole tree) · ③ It never loaded when I ran both entry paths (*proven*, tracer) · ② **Outside callers not checked.** Its docstring says "superseded by the plugins" | Confirm no ops script or other service imports it, then delete in one commit |
| `app/models/notify.py` (`subject`) | **watch**, strong candidate | ① No references (*traced*) · ③ It never loaded (*proven*) · ② **Outside callers not checked** | Same. Deleting it also removes the only layer breach |
| `app/plugins/csv_out.py` / `render` | **live, keep** | The script calls it unused, but `registry.py:4` loads it by name through `importlib`. The tracer loaded it and `render` returned output (*proven*) | None |
| `app/routes/web.py` / `handle` | **live, keep** | It is the app's entry point and runs `place_order` → `save` (*proven*, tracer). Nothing in the repo calls it, so something outside the repo does | None |
| `app/registry.py` / `load` | **live, keep** | Nothing in the repo calls it either. Like `handle`, it's an externally called entry point | None |
| `notify.py:2` imports `app.routes.web.BANNER` | **layer breach** (*proven*) | The data layer reaches up into the interface layer to get a string constant, so `notify` can't load without importing the web layer and the whole order stack | Delete `notify.py` if it's confirmed dead. If it has to stay, move `BANNER` into models or config, or change the declared layers (your call) |

## What would finish the proof
The same pattern that keeps `handle` and `load` alive matters for the two candidates: this code is called from outside the repo. Before deleting either file, search the deploy scripts, cron jobs, other repos and any runbooks for `legacy_export`, `to_xml`, `notify` and `subject`. If nothing turns up, delete them one commit per file so either can be reverted on its own.

## Notes
- `ARCHITECTURE.md` doesn't assign `app/plugins/` or `app/registry.py` to any layer, so imports from those modules weren't checked against the layer order. There's a gap in the architecture spec, not a violation.
- There are no tests anywhere, so the tracer only exercised the two paths I drove by hand.
- Bugs I passed, not chased:
  - `legacy_export.py:5` builds XML without escaping, so row data can inject markup. This goes away if the file is deleted.
  - `csv_out.py:5` doesn't quote or escape values, so values containing commas or newlines will corrupt the CSV.
  - `order.py:2` stores orders in a module-global in-memory list. They are lost on restart and not safe under concurrent requests.

<details><summary>Script output (with layers)</summary>

```
GRAPH — 12 modules, 3 import edges traced.
LAYER BREACHES (proven) — declared order: interface > domain > data
  app/models/notify.py:2  app.models.notify (data) -> app.routes.web (interface)
  note: 4 modules match no declared layer: app.__init__, app.plugins.__init__, app.plugins.csv_out, app.registry
DEAD MODULE CANDIDATES (suspected): app.models.notify, app.services.legacy_export
UNUSED DEFS (suspected): handle, render, subject, to_xml
```
Tracer: after calling `web.handle(...)` and `registry.load()`, the only loaded `app.*` modules were `models.order`, `plugins.csv_out`, `registry`, `routes.web` and `services.orders` (plus the package `__init__`s).
</details>

I haven't modified anything; the layers file is at `/tmp/layers.txt`. Once you confirm there are no outside callers, I can do the two deletions.