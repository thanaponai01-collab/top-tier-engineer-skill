I read all 13 files in `fixture/` (56 lines in total) and searched for every module and function name. Nothing in `fixture/` runs the app: there's no entry point, test, config or git history. So "unreferenced" below means unreferenced inside this folder. Outside code could still call these modules. I haven't deleted anything.

## Can go

**`app/services/legacy_export.py`** is the clearest case.
- Its own docstring says it was replaced by the plugins and that nothing references it.
- Nothing imports it, and the strings `legacy_export` and `to_xml` don't appear anywhere else, so `registry.py` can't be loading it by name either.
- Only keep it if something outside this folder calls `to_xml`.

**`app/models/notify.py`** can probably go.
- Nothing imports it or calls `subject()`.
- It also breaks the layering rule in `ARCHITECTURE.md`: a data-layer module imports `BANNER` from `app/routes/web.py`, which is the interface layer (`notify.py:2`).
- Deleting it fixes the only layering violation in the code.
- If it turns out to be used somewhere, keep it but fix the dependency: move `BANNER` down into models (or into a shared constants module), or move `subject()` up into services or routes.
- I'm less sure about this one than `legacy_export.py`, because nothing says it's obsolete. It just looks unused.

## Looks dead but is still needed

- **`app/plugins/csv_out.py`**: nothing imports it, but `registry.py:4` loads it by name through `ENABLED_PLUGINS`. A search for imports won't find this, which is exactly how it could get deleted by mistake. Keep it.
- **`app/registry.py`**: nothing in the repo calls `load()`, but `ARCHITECTURE.md` documents it as how plugins are found. Its caller is presumably outside this folder. Keep it.
- **`app/routes/web.py`, `app/services/orders.py`, `app/models/order.py`**: these form the working path from `handle()` through `place_order()` to `save()`. `handle()` has no caller here, which is normal for the interface layer. Keep them.
- **The empty `__init__.py` files**: they make the folders proper Python packages. They cost nothing, so keep them.

**Before deleting:** search the code that actually deploys or imports this package for `legacy_export`, `notify` and `subject`, including any string-based imports. If that comes back clean, both files can go. I can delete them, or apply the layering fix to `notify.py` instead.