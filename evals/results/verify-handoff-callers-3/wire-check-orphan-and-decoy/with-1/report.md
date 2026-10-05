# wire-check report: `fixture/`, whole-system mode

**First break:** `handlers/export.py` is loaded at startup but never routed. `GET /export` returns 404 (proven). It is the only orphan. `digest` is reached only through a string lookup, so I've marked it unknown and then proven it by running it. Nothing was changed.

## Entry points

I found two: the web entry `app.py` (`dispatch` goes through `routes.ROUTES`) and the cron entry `scheduler.py` (`run_all` goes through `settings.SCHEDULED_JOBS`). The other places I checked had no entry points: no CLI, message consumer or build hook. The inventory came from the glob of `fixture/`, which found 3 handlers (`health`, `export`, `digest`). The served set came from walking forward from the two entry points.

## Results

| Component | Surface | Exists | Registered | Routed | Invoked | Reachable | Verdict |
|---|---|---|---|---|---|---|---|
| `health.check` | web | ✅ proven | ✅ `routes.py:2` | ✅ `"/health"` | ✅ proven | ✅ `(200, 'ok')` | **Served** |
| `export.run` | web | ✅ proven | ✅ `handlers/__init__.py:2` (loaded, never used) | ❌ no `ROUTES` entry | ⛔ blocked | ⛔ blocked | **Orphaned**. `/export` returns 404 (proven) |
| `digest.run` | cron | ✅ proven | ✅ by string `"handlers.digest:run"` in `settings.py:3` | n/a (cron, no route) | ✅ proven: `scheduler.py` exit 0, and the spec resolves to `(200, 'digest sent')` | ⚠️ see below | **Served, was UNKNOWN**. No import mentions it, so a static walk can't follow it. |

**Unknown count:** 1 (`digest`), and I resolved it by running it. Nothing is left unknown, but the string-based lookup is why a grep-based audit would wrongly call `digest` dead.

- **`export` is not served.** Its `__init__` import makes it look wired, but that import only loads the module. `routes.py` is the only thing that maps a path to a handler, and it has one entry.
- **`digest` effect (suspected).** `scheduler.run_all` discards the return value, and `run()` only returns a tuple. It sends nothing, so I can't confirm the digest actually goes out. The stub body is also why link 5 is not confirmed. Please check this with the owner.
- **Silent failure risk.** `run_all` has no error handling. A typo in `SCHEDULED_JOBS` would raise `ImportError` or `AttributeError`, and the first bad job would stop every job after it.

## Connecting code (proposed, not applied)

`export` is complete, so this is a decision for the owner: wire it up, or delete it. To wire it:

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

Proof is `python -c "import app; print(app.dispatch('/export'))"`, which should print `(200, 'id,total\n1,42')`.

## Recommendation

Add a wiring test that fires the real triggers, so no file can be added without being reached. For each module in `handlers/` except `__init__`, assert that it is either a value in `ROUTES` or named in `SCHEDULED_JOBS`. Also resolve every `SCHEDULED_JOBS` spec with `importlib`. That catches `export`-style orphans and typos in cron strings, and it needs no framework.

## For the handover

Tell the receiving team three things:
1. `/export` is dead, and it is unclear whether that is intended.
2. The cron job's names are only strings in `settings.py`.
3. `digest` and `export` are stubs with hardcoded data, not real implementations.