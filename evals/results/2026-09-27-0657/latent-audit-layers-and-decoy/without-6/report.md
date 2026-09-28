I looked over all 13 files in `fixture/` (56 lines of code) and searched for every module and function name. There's no git history or test suite, so this is based only on the code as it stands. I haven't deleted anything.

## Safe to remove

**1. `app/services/legacy_export.py`**
- Nothing imports it, and nothing mentions `legacy_export` or `to_xml` anywhere, not even as a string.
- That rules out the runtime-by-name loading that `registry.py` does.
- Its own docstring says the plugins replaced it.

**2. `app/models/notify.py`**
- Nothing imports it or calls `subject()`.
- It also breaks the layering rule in `ARCHITECTURE.md`: a data-layer module imports `BANNER` from `app/routes/web.py`, which is the top layer.
- Deleting it removes the only layering violation in the code. If a notification subject line is ever needed, it belongs in `services/` or `routes/`.
- Once it's gone, `BANNER` in `web.py:4` has no users either, so it can go too.

## Looks unused but must stay

**`app/plugins/csv_out.py`**
- Nothing imports it, but `registry.py:4` loads it at runtime by name through `ENABLED_PLUGINS` with `importlib`.
- `ARCHITECTURE.md` says this is deliberate.
- Deleting it would pass any static unused-code check and then crash when `registry.load()` runs.

**`registry.load()` and `routes/web.py:handle()`**
- Nothing in `fixture/` calls either one. But `handle` is the HTTP entry point and `load` is the plugin loader, so both are almost certainly called from outside this directory (a server or framework).
- Keep them, and keep everything they reach: `services/orders.py` and `models/order.py`.

## One caveat

Plugins are looked up by string, so "nothing references it" can't be fully proven from inside `fixture/`. Before deleting the two files, grep any deployment config or other repos that might set `ENABLED_PLUGINS` or import `app.*` by name. If that search comes back clean, both deletions are low-risk.

Want me to delete `legacy_export.py`, `notify.py` and the leftover `BANNER` constant?