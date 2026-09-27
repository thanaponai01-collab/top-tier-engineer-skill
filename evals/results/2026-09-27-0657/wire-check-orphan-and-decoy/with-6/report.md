**Verdict:** one real orphan. `handlers/export.py` is a finished CSV export that loads at startup but has no route, so no request can reach it. `GET /export` returns 404 (**proven**). One more item is **unknown** and matters for the handoff: nothing in `fixture/` shows that `scheduler.py` is ever run by cron. That means I can't say whether the nightly digest runs in production.

I changed nothing. The connecting code is below for you to decide on.

## Ways in (counted first)

| Entry kind | Instance | Evidence |
|---|---|---|
| Web request | `app.py` → `dispatch()` → `routes.ROUTES` | proven: `python3 app.py` → `(200, 'ok')` |
| Schedule | `scheduler.py` → `run_all()` → `settings.SCHEDULED_JOBS` via `importlib` | proven when run by hand. What starts it (crontab, systemd timer, k8s CronJob) isn't in the tree, so it's **UNKNOWN** |
| CLI / message / other service / build step | none found | searched all 8 files in `fixture/` and the parent directory |

## Inventory (from the source) vs. served set (from walking the entry points)

Inventory: `health.check`, `export.run`, `digest.run`. Served, walking forward: `health.check` (web) and `digest.run` (scheduler, reached by name in a string). Orphan = `export.run`.

| Component | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Status | Evidence | Proposed outcome |
|---|---|---|---|---|---|---|---|---|
| `handlers/health.py:check` | ✅ | ✅ `routes.py:2` | ✅ `/health` | ✅ | ✅ returns `(200,'ok')` | **served** | proven (ran `app.py`) | keep |
| `handlers/export.py:run` | ✅ | ✅ imported in `handlers/__init__.py:2` | ❌ not in `ROUTES` | ⛔ | ⛔ | **orphaned: not routed** | proven (`dispatch('/export')` → 404; `handlers.export` is in `sys.modules`) | wire it, or decide it's dead and delete it: owner's call |
| `handlers/digest.py:run` | ⚠️ | ✅ `settings.py:3`, string only | ❓ depends on an external cron | ✅ when `run_all()` runs | ⚠️ return value dropped | **unknown** | proven that `run_all()` calls it (patched and counted 1 call); the cron trigger is unproven | confirm the cron entry before handoff |

## Findings

**1. Export has no route (orphan, not routed).** It's easy to miss because the handler *is* imported at startup (`handlers/__init__.py`), so it looks wired. But imported only counts as registered. Requests reach handlers only through the `ROUTES` dict, and export was never added to it. Proposed fix (not applied; the `/export` path is my guess):

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

**2. Digest: the trigger is unknown and the job is probably a stub** (*suspected*). `digest.run()` only returns `(200, "digest sent")` and doesn't send anything. `scheduler.run_all()` also throws away the return value (`scheduler.py:11`), so if it failed, nobody would see it. Before handoff, answer two things:
- Where is the cron entry? Run `crontab -l`, or check the deploy config for `python scheduler.py`. If there isn't one, the digest never runs.
- Is the nightly digest supposed to send something real? If so, the code for that isn't written yet.

## What would have caught this

Add a test that checks the handler inventory against the served set. List every public function in `handlers/*.py`, then assert that each one is a value in `routes.ROUTES`, or is named in `settings.SCHEDULED_JOBS`, or is on an explicit allowlist. Any handler added without a route or schedule would then fail CI instead of shipping as dead weight. It would also show that the scheduled path depends on a string lookup, which is why the digest never shows up in an import search.