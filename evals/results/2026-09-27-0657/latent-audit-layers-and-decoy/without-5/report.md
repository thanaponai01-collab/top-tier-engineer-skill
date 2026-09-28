Short answer: two files can probably go, and one file that looks dead has to stay.

The fixture is small: 7 Python modules and `ARCHITECTURE.md`. I read all of it and searched for every module and function name, including string references.

## Can go

**1. `app/services/legacy_export.py`**
- Nothing imports it, and neither `to_xml` nor `legacy_export` appears anywhere else, not even as a string.
- Its own docstring says the plugins replaced it.
- It isn't in `ENABLED_PLUGINS`, so the registry can't load it either.

**2. `app/models/notify.py`**
- Nothing imports `notify` or calls `subject()`.
- It also breaks the rule in `ARCHITECTURE.md`. It's in the data layer but imports `BANNER` from `app/routes/web.py` in the interface layer. That makes a loop (routes → services → models → routes), which will cause a circular import if anything ever imports it. Deleting it removes the only layering violation in the code.
- If someone does need that subject line later, it belongs in `routes/` or `services/`, not `models/`.

## Looks unused but must stay

**`app/plugins/csv_out.py`**: no import statement mentions it, so a dead-code tool or a grep for imports would flag it. But `registry.py` loads it by name through `importlib` (`ENABLED_PLUGINS = ["app.plugins.csv_out"]`). Deleting it would make `registry.load()` fail at runtime.

## Also stays

- **`app/registry.py`**: nothing in the repo calls `load()`, but it's how plugins are meant to be loaded, per `ARCHITECTURE.md`.
- **`app/routes/web.py`**: nothing calls `handle()` either. It's the HTTP entry point, and the only user of `place_order` and `order.save`.
- **`services/orders.py` and `models/order.py`**: both are used by `handle()`.
- **The `__init__.py` files**: they're empty, but they make these regular packages. Keep them.

## One caveat

There's no app entry point, server setup or tests in `fixture/`, so `handle()` and `registry.load()` must be called from outside. That means I can't rule out outside code importing `legacy_export` or `notify` too. It's worth a quick search of any code that uses this package before deleting them.

I haven't changed anything. This folder isn't a git repository, so a deletion can't easily be undone. Do you want me to delete the two files?