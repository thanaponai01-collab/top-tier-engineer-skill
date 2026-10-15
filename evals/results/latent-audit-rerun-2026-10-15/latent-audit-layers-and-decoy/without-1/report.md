**Short answer:** you can safely delete one file, `app/services/legacy_export.py`. A second file, `app/models/notify.py`, also looks unused, but it should be fixed or removed for a different reason. Everything else is in use, including the plugin that looks unused.

I read all 13 files in `fixture/` and searched for every symbol each module defines.

### Safe to delete
- **`app/services/legacy_export.py`**: nothing references the module or `to_xml`, either by import or by string. Its docstring says it was replaced by the plugins, and `ARCHITECTURE.md` agrees. It isn't in `ENABLED_PLUGINS`, so the registry can't load it either.

### Probably delete, and it breaks the layering rule anyway
- **`app/models/notify.py`**: nothing calls `subject()`. It also imports `BANNER` from `app/routes/web.py`, so the data layer reaches up into the interface layer, which `ARCHITECTURE.md` forbids. If nobody outside this repo uses it, delete it. If someone does, move `BANNER` down into `models` (or a shared constants module) and have `routes/web.py` import it from there.

### Looks unused but is needed: don't delete
- **`app/plugins/csv_out.py`**: no import statement mentions it. That's on purpose: `app/registry.py` loads it at runtime through `importlib` using the string `"app.plugins.csv_out"` in `ENABLED_PLUGINS`. A dead-code tool or an import search will flag it as unused. Deleting it would break `registry.load()` at runtime, not at import time.
- **`app/registry.py`**, **`app/routes/web.py`**: nothing in `fixture/` calls `load()` or `handle()`. They look like entry points called from outside this directory (an app server, a CLI). I can't see that wiring from here, so check before treating them as dead.

### In use
- `routes/web.py` → `services/orders.py` → `models/order.py` is the main order path, and every import goes down a layer as it should.
- The empty `__init__.py` files are needed as long as these are regular packages.

I haven't changed anything. Do you want me to delete `legacy_export.py`, and either delete `notify.py` or fix its import?