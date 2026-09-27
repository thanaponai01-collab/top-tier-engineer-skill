Short answer: two files can go, `app/services/legacy_export.py` and `app/models/notify.py`. Everything else is in use, even where a quick search makes it look unused. I only read and searched the code; I didn't delete anything.

## Can go

**1. `app/services/legacy_export.py`**
- Nothing in the repo mentions `legacy_export` or `to_xml`, either as an import or as a string. That matters because the plugin loader finds modules by name from a string list (`ENABLED_PLUGINS` in `app/registry.py:4`), so I checked strings too.
- Its docstring says the plugins replaced it, and `csv_out` is the export that's actually wired up.

**2. `app/models/notify.py`**
- Nothing imports it, and nothing calls `subject()`.
- It also breaks the rule in `ARCHITECTURE.md`: a data-layer module imports `BANNER` from the routes layer (`app/models/notify.py:2`). That's a lower layer reaching up into a higher one. Deleting the file removes the only layering violation in the repo.
- If someone does want order-notification subjects later, the right place is `services/`, not `models/`.

## Looks unused but keep

- **`app/plugins/csv_out.py`**: no import statement mentions it, but `registry.load()` loads it at runtime through `importlib`, using the name in `ENABLED_PLUGINS`. Deleting it would break `load()` with an `ImportError`. The rule of thumb is that a plugin is only dead once it's also removed from `ENABLED_PLUGINS`.
- **`app/registry.py`**: nothing in the repo calls `load()`, but `ARCHITECTURE.md` names it as the way plugins get loaded, so the caller is probably outside this code.
- **`app/routes/web.py`** (`handle`, `BANNER`): nothing in the repo calls `handle()` either, but it's the HTTP entry point, so something external presumably calls it. `BANNER` has no users once `notify.py` is gone. It's a one-line constant, so drop it or keep it as you like.
- **`services/orders.py` and `models/order.py`**: the live request path (`handle` → `place_order` → `save`).

## One caveat

The repo has no entry point, tests, or deployment config, so I can't see which code outside it calls `handle()`, `load()`, or anything else. If any other code imports this package, run a quick search there for `legacy_export`, `notify`, and `subject` before deleting.

If you want, I can delete the two files (and `BANNER` if you'd like it gone).