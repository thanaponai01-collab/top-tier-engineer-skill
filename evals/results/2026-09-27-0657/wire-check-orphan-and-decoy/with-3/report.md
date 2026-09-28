**Verdict:** one handler is orphaned. `handlers/export.py` (the CSV export of order totals) is complete and loads at startup, but no route points to it, so requests can't reach it. `GET /export` returns 404 (proven). One more item is **unknown** rather than orphaned: the nightly digest works when `scheduler.py` runs, but nothing in the repo or on this machine starts `scheduler.py`. Whatever cron job or external caller runs it isn't in this code. Ask the current owners where it's configured before the handoff.

Also, the docstring in `app.py` says the process "starts here and nowhere else". That's wrong: `scheduler.py` is a second entry point. The receiving team should know that.

## Ways in (counted before the walk)

| Entry kind | Instance | Evidence |
|---|---|---|
| Web request | `app.py` → `dispatch()` → `routes.ROUTES` | proven: `python3 app.py` → `(200, 'ok')` |
| Schedule | `scheduler.py` → `run_all()` → `settings.SCHEDULED_JOBS` → `importlib` | proven when run by hand. **What triggers it is UNKNOWN**: no crontab, Procfile or unit file in `fixture/`, and none in `/etc/cron*` or systemd on this box |
| CLI / message / other service / build | none found | traced (all 8 files read) |

## Inventory vs. served set

The inventory comes from the source files, not the walk: `health.check`, `export.run`, `digest.run`, plus the two entry functions.

| Component | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Status | Evidence |
|---|---|---|---|---|---|---|---|
| `handlers/health.py:check` | ✅ | ✅ `routes.py:2` | ✅ `/health` | ✅ | ✅ `(200,'ok')` | **served** | proven |
| `handlers/export.py:run` | ✅ | ✅ imported in `handlers/__init__.py:2` (loaded: `True`) | ❌ **not in `ROUTES`** | ⛔ | ⛔ | **orphaned: not routed** | proven: `dispatch('/export')` → `404` |
| `handlers/digest.py:run` | ✅ | ✅ by string, `settings.py:3` (no import anywhere, found through `importlib`) | ✅ `scheduler.run_all` | ✅ `(200,'digest sent')` when `run_all()` is called | ✅ in-process | **unknown**: the chain works, but whether anything fires `scheduler.py` isn't known | proven from `run_all()` onward; the trigger is unfollowable |

A trap to note: a check based on imports would flag `digest` as dead, because no import names it, and would call `export` alive, because it's imported. Both would be wrong.

## Connecting code (not applied)

Your request was a report, and the skill says not to connect anything without being asked. The fix for `export` is one line, but the URL path is my guess. Confirm it with whoever uses the export:

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

The other option: if nobody uses the export, delete `handlers/export.py` and its import in `handlers/__init__.py`. That's for the owner to decide, since routing it would expose order totals on a new URL.

For `digest`, no code is missing. What's missing is where the trigger lives. Get the cron or scheduler definition from the current team and put it in the repo (a crontab file or deploy config) so the handoff includes it.

## Recommendation

Add a startup test that checks every `run` or `check` function under `handlers/` is either a value in `ROUTES` or named in `SCHEDULED_JOBS`, and fails on anything else. It would have caught `export`, and it would keep `digest` from being deleted later as "unused".