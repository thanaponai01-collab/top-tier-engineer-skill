I read all 13 files under `fixture/` and searched for every module and function name. There are no tests, no entry point and no git history, so everything below comes from reading the code. I haven't deleted anything.

## Can go

**`app/services/legacy_export.py`**
- Nothing imports it or mentions its name. Its own docstring says the plugins replaced it.
- It isn't loaded by name at runtime either: `ENABLED_PLUGINS` in `app/registry.py:4` lists only `app.plugins.csv_out`, and this file isn't in `app/plugins/` anyway.
- The one risk is outside code calling `app.services.legacy_export.to_xml` directly. If nothing outside this repo imports from `app`, delete it.

**`app/models/notify.py`** (probably)
- Nothing in the repo imports `notify` or calls `subject()`.
- It also breaks the rule in `ARCHITECTURE.md`: a data-layer module (`models/`) imports `BANNER` from the interface layer (`routes/web.py`). If `routes/web.py` ever imports it, the imports will loop: `routes → services → models → routes`.
- If nobody outside needs it, delete it. If something does, keep `subject()` but move the `"orders"` string into `models/` (or pass it in as an argument) so the import points the right way.

## Keep, even though it looks unused

**`app/plugins/csv_out.py`**
- No import statement mentions it, so a tool that only follows imports would flag it as dead. It isn't: `registry.load()` loads it by name at runtime. The string `"app.plugins.csv_out"` in `ENABLED_PLUGINS` is its only reference.
- If you delete it, `load()` fails with an `ImportError` at runtime. Nothing will catch it before then.

**`app/registry.py`, `routes/web.py` → `services/orders.py` → `models/order.py`**
- Nothing in the repo calls `load()` or `handle()` either. But they look like the entry points the web framework or app startup calls, which live outside this folder. Code that nothing calls from inside the repo is exactly what entry points look like, so that isn't evidence they're dead.
- The chain from `handle()` down to `save()` is the app's main path.

**The empty `__init__.py` files**
- They make the folders importable as packages, which the `importlib` lookup and the absolute imports rely on. Keep them.

## Summary

| File | Verdict |
|---|---|
| `services/legacy_export.py` | Delete |
| `models/notify.py` | Delete, or fix the upward import if it's still needed |
| `plugins/csv_out.py` | Keep (loaded by name at runtime) |
| Everything else | Keep |

Before deleting, it's worth searching whatever deploys or imports this package (other repos, config files, scripts) for `legacy_export`, `notify` and `csv_out`, since this repo can't show callers from outside it. Want me to go ahead and remove the two files?