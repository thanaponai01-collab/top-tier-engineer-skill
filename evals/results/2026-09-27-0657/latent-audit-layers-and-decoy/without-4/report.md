I read all 8 source files in `fixture/` and grepped for every name they define. Nothing here calls anything else from outside, so there's no entry point (no `main`, no app wiring). That means "unreferenced" only shows that nothing inside this repo uses a piece of code. Something outside it, like a web framework, a deploy config or another repo, could still be calling it.

**Safe to delete:**
- **`app/services/legacy_export.py`**: nothing mentions the module or its `to_xml` function, and it has no dynamic loading path. Its own docstring says the plugins replaced it. Before deleting, check any external XML consumers once, since `grep` can't see those.

**Looks unused, but must stay:**
- **`app/plugins/csv_out.py`**: no import statement mentions it, but `app/registry.py:4` loads it at runtime by its name as a string (`ENABLED_PLUGINS`). An "unused import" tool would flag it wrongly. Keep it as long as the registry lists it.
- **`app/registry.py`**: nothing calls `load()` in this repo. It's the documented way plugins get loaded (`ARCHITECTURE.md:9`), so it's most likely called from outside the repo. Keep it unless you confirm nobody calls it.
- **`app/routes/web.py` `handle()`**: no callers here, but it's the HTTP entry point, so something outside the repo calls it. It is the only path into `services/orders.py` and `models/order.py`, which makes that whole chain in use.

**Not dead, but wrong: `app/models/notify.py`**
- Nothing calls `subject()` either. The bigger issue is that it imports `BANNER` from `app.routes.web`, so the data layer reaches up into the interface layer. That breaks the rule in `ARCHITECTURE.md:3`. It's also one step away from a circular import: once the services or models chain imports `notify`, you get routes → services → models → routes.
  - If nothing outside the repo uses `subject()`, delete `notify.py`.
  - If something does, move `BANNER` down into `models` (or into a shared constants module) and have `web.py` import it from there.

**Minor:** the empty `__init__.py` files are needed for the `app.*` package imports and the `importlib` string lookup, so leave them.

**In short:** delete `legacy_export.py` now. Delete `notify.py`, or fix its layering, depending on whether anything outside the repo uses it. Keep everything else. I haven't changed anything; tell me if you want me to make these edits.