I read all 13 files in `fixture/` (56 lines of code) and searched for every module and function name, including names that only appear inside strings. There's no git history and no tests, so this is based only on what's in the code.

## Can go

**`app/services/legacy_export.py`**
- Nothing imports it or mentions it by name, not even as a string. It isn't in `ENABLED_PLUGINS` and isn't under `app/plugins/`, so the registry can never load it.
- Its own docstring says the plugins replaced it.
- **Safe to delete**, unless something outside this repo imports `app.services.legacy_export` directly (an old script or cron job, say). I can't check for that from here.

**`app/models/notify.py`, and then `BANNER` in `app/routes/web.py:4`**
- Nothing imports `notify` or calls `subject()`.
- It also breaks the layering rule in `ARCHITECTURE.md`: it's in the data layer but imports from the interface layer (`from app.routes.web import BANNER`). This is the only layering violation in the repo, so deleting it fixes that too.
- `notify` is the only user of `BANNER`. If `notify` goes, `BANNER` is unused and can go as well.
- One judgement call: if someone actually wants order notification subjects, this isn't dead so much as half-built. The subject text should then live in `models/` or `services/`, not be pulled up from `routes/`. Either way, the current version shouldn't stay as it is.

## Looks dead but is load-bearing — keep

**`app/plugins/csv_out.py`**
- No import statement mentions it, but `app/registry.py:4` lists it by name in `ENABLED_PLUGINS` and loads it at runtime with `importlib`. `ARCHITECTURE.md` says this is how plugins are meant to work.
- A tool that only follows imports would call it dead. Deleting it would make `registry.load()` raise `ModuleNotFoundError`.

**`app/registry.py`**
- Nothing in the repo calls `load()`. But nothing calls `routes/web.handle()` either, so both are presumably wired up by whatever runs the app (a server or framework), which isn't in this fixture.
- It's the documented plugin mechanism, so keep it. Before deleting it, I'd confirm whether whatever runs the app calls it.

**The rest:** `routes/web.handle` → `services/orders.place_order` → `models/order.save` is the main request path, and all of it is used. The empty `__init__.py` files mark the folders as packages; leave them.

## Net result
Delete `legacy_export.py` and `notify.py`, and remove `BANNER` from `web.py`. That's about 12 lines and fixes the layering violation.

I haven't changed anything. Do you want me to make those deletions?