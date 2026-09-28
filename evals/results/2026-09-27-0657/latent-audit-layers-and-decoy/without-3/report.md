I read all 13 files (56 lines of code) and searched for every module and function name. I didn't delete or change anything. One caveat applies throughout: nothing in `fixture/` has an entry point. No file calls `routes.web.handle()` or `registry.load()`, so something outside this directory must call them. "Unreferenced" below means unreferenced inside `fixture/`.

## Safe to delete

**`app/services/legacy_export.py`**
- Nothing imports `legacy_export` or calls `to_xml` anywhere in the tree, and its docstring says it was replaced by the plugins.
- Since it lives in `services/` and not `plugins/`, `registry.py` can't load it by name either.
- One last check before deleting: search any code outside `fixture/`, and any config or deploy files, for the string `legacy_export`. If nothing turns up, delete it.

## Probably delete, and fix it either way

**`app/models/notify.py`**
- Nothing imports it or calls `subject()`.
- It also breaks the layering rule in `ARCHITECTURE.md`: it's in the data layer but imports `BANNER` from `app.routes.web` (interface layer).
- That import is also a circular-import risk: `routes → services → models → routes`. It doesn't break today only because nothing imports `notify`.
- If nothing outside the repo uses it, delete it. If something does, move it to `services/` (or move `BANNER` somewhere lower) so it no longer imports upward.

## Looks unused but must stay

**`app/plugins/csv_out.py`**
- A search finds no imports of it, but `registry.py:4` loads it at runtime by its dotted name `"app.plugins.csv_out"`.
- Deleting or renaming it would break `registry.load()` with an `ImportError`. `ARCHITECTURE.md` describes this setup on purpose.

**`app/registry.py`**
- Nothing in `fixture/` calls `load()`, but it's how the plugins get loaded (per `ARCHITECTURE.md`), so something external almost certainly calls it. Keep it unless you can show nothing does.

## Clearly still used

- `routes/web.py` → `services/orders.py` → `models/order.py`: this is the order-handling path and every link in it is used.
- `BANNER` in `routes/web.py` is only used by `notify.py`. If you delete `notify.py`, `BANNER` becomes dead as well.
- The empty `__init__.py` files keep the packages importable. Leave them.

**What I'd do:** delete `legacy_export.py` now. Delete `notify.py` and `BANNER` together once a check outside `fixture/` confirms nothing uses them. Keep `csv_out.py` and `registry.py` even though they look orphaned. I can make these changes if you want.