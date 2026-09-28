**Verdict:** one real orphan and one unresolved unknown. `handlers/export.py` (the CSV export of order totals) loads at startup, but no route points to it, so no request can reach it. The nightly digest is registered, but nothing in this repo shows what runs the scheduler, and when it does run it doesn't actually send anything. Only `/health` is proven to be served.

## Ways in (counted first)

| Entry | Instances | How found |
|---|---|---|
| Web request | `app.py` → `routes.ROUTES` (dict with 1 route) | read + ran |
| Schedule | `scheduler.py` → `settings.SCHEDULED_JOBS` via `importlib` (1 job) | read + ran |
| Message, CLI, other service, build step | none found | only the 8 `.py` files exist. There is no crontab, Procfile, unit file or Dockerfile |

The inventory comes from `find fixture -type f`: 3 handler functions plus the wiring modules. The served set comes from running each entry point. Orphans are the inventory minus the served set.

## Results

| Surface | Status | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Evidence | Proposed outcome |
|---|---|---|---|---|---|---|---|---|
| `handlers/health.check` | **served** | ✅ | ✅ `routes.py:2` | ✅ `/health` | ✅ | ✅ `(200, 'ok')` | proven: `python3 app.py` | none |
| `handlers/export.run` | **orphaned** | ✅ | ✅ imported by `handlers/__init__.py:2`; `sys.modules` confirms it loads | ❌ **no entry in `ROUTES`** | ⛔ | ⛔ | proven: `dispatch('/export')` → `(404, 'not found')` | **Not routed.** Add the route, or have the owner confirm it's dead and delete it |
| `handlers/digest.run` | **unknown** | ⚠️ body is a stub | ✅ only by string in `settings.py:3`, loaded with `importlib` | ❓ **what runs `scheduler.py` is outside the repo** | ✅ when `run_all()` is called | ❌ **nothing is sent. The return value is thrown away in `scheduler.py:11`** | proven: `run_all()` imports and calls it. Trigger unknown | **Effect lost.** Confirm the cron trigger, and implement or retire the send |

Notes:
- **export is a false "loaded = live".** Importing it in `handlers/__init__.py` makes it look wired, but `app.dispatch` only goes through `ROUTES`. A plain grep for imports would count it as used. It isn't.
- **digest is the opposite trap.** No import statement mentions it, so an import-graph tool would call it dead. It is reachable, by a string in `settings.py`. Don't delete it on a tool's say-so.
- **Unknowns: 1.** That's the external trigger for `scheduler.py`. Nothing in `fixture/` schedules it. Whoever runs production needs to show the crontab, k8s CronJob or equivalent. Until then, "the digest runs nightly" is unverified.
- **The digest doesn't do anything.** `run()` returns the string `"digest sent"` without sending anything, and `run_all()` ignores whatever it returns. Even if cron fires, no email or message goes out. This is a live bug that looks like working code, and the most important point for the receiving team.

## Connecting code (proposed, not applied; you asked for a report)

Wire export, assuming `/export` is the intended path:

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

Stop the scheduler throwing results away, so a stub or failing job shows up in logs:

```python
# scheduler.py, inside run_all()
        result = getattr(module, func_name)()
        print(f"{spec} -> {result}")
```

The actual digest sending can't be written from this code. The owner has to say what "digest" should send, and to whom.

## Handover checklist for the other team

1. Get the production scheduler config that invokes `scheduler.py`. It's the only unknown.
2. Decide whether `/export` should be routed or deleted.
3. Treat the digest as not implemented.

## Recommendation

Add a startup assertion or test that every module in `handlers/` is referenced by either `ROUTES` or `SCHEDULED_JOBS`, and that every `SCHEDULED_JOBS` spec resolves with `importlib`. That one check would have caught export and would protect digest from being deleted as "dead". The trigger itself also belongs in the repo (e.g. a checked-in crontab), so the schedule entry point can be traced at all.