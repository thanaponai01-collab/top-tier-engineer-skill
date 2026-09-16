# Wire Check — fixture/

**First break: `handlers/export.py` is loaded but nothing routes to it.**

There are two entry points, not one: `app.py` (request dispatch through
`routes.py`) and `scheduler.py` (cron, resolving job names with `importlib`).

| component | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | evidence |
|---|---|---|---|---|---|---|
| `handlers/health.py` | ✅ | ✅ | ✅ | ✅ | ✅ | proven — `app.py` returned `(200, 'ok')` |
| `handlers/export.py` | ✅ | ✅ | ❌ | ⛔ | ⛔ | proven — no entry in routes.py |
| `handlers/digest.py` | ✅ | — | UNKNOWN | UNKNOWN | UNKNOWN | traced — named by string in `settings.py` |

`handlers/export.py` is imported by `handlers/__init__.py`, so it loads, but
`ROUTES` in `routes.py:4` has one key. No route maps to it: link 3 fails and
links 4–5 are blocked, not failed.

`handlers/digest.py` is not orphaned. No import statement mentions it, but
`settings.py` names it in `SCHEDULED_JOBS` and `scheduler.py` resolves that
string with `importlib.import_module` and `getattr`. Unfollowable by import
graph alone, so it is UNKNOWN until the cron entry point is counted — and once
it is, it is served.

Fix: add `"/export": export.run` to `ROUTES`.
