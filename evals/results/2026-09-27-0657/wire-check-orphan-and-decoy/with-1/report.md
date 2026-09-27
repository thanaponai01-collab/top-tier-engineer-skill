The service has one orphan: **`handlers/export.py` (the CSV export) loads at startup, but no route or job ever calls it.** `/export` returns 404 (proven). The nightly digest looks orphaned to a grep, but it is served. The scheduler loads it by name at runtime, and I ran that path. Two things are still unknown and should go on the handoff list:

- Nothing in `fixture/` shows who runs `scheduler.py`. The cron entry lives outside this code.
- The digest's result is thrown away, and its body sends nothing.

I changed no code. The only thing I touched was deleting the `__pycache__` folders my test runs created.

## Ways in
| Entry | Instances | Evidence |
|---|---|---|
| Web process (`app.py` → `routes.ROUTES`) | 1 route: `/health` | proven: `python3 app.py` → `(200, 'ok')` |
| Cron (`scheduler.py` → `settings.SCHEDULED_JOBS`, loaded by name at runtime) | 1 job: `handlers.digest:run` | proven: `run_all()` called `digest.run` |
| Whatever runs `scheduler.py` (crontab, k8s CronJob, etc.) | **not in `fixture/`** | **UNKNOWN** |

I built the list of everything that exists from the 8 source files, separately from the walk out from the entry points. Anything on the first list but not reached by the walk is an orphan.

## Whole-system table
| Component | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Status | Evidence | Proposed outcome |
|---|---|---|---|---|---|---|---|---|
| `health.check` | ✅ | ✅ `routes.py:2` | ✅ `/health` | ✅ | ✅ returns 200 | **served** | proven | none |
| `export.run` | ✅ | ✅ `handlers/__init__.py:2` (proven it's in `sys.modules`) | ❌ no entry in `ROUTES` | ⛔ | ⛔ | **orphaned: not routed** | proven (`dispatch('/export')` → 404) | wire it, or the owner decides to delete it |
| `digest.run` | ✅ | ✅ by name in `settings.py:3` | ✅ `SCHEDULED_JOBS` | ✅ via `run_all()` | ❌ `scheduler.py:11` drops the return value; the body only returns the string `"digest sent"` and doesn't send anything | **served, but no effect lands** | proven that it's invoked; the missing effect is traced | fix it before handoff (it looks like a live bug, not dead code) |
| `scheduler.py` itself | ✅ | n/a | ? external cron | ? | ? | **UNKNOWN** | suspected | get the crontab or deploy config from the current owners |

The export was probably missed because its module is imported in `handlers/__init__.py`, so it looks wired. But being imported is only link 2; the route table is link 3, and `/export` isn't in it.

## Connecting code (proposed, not applied)
`routes.py`:
```python
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```
For the digest: `run()` has to actually deliver the digest. `run_all()` should log or raise on a failed result instead of discarding it. Only the owner can say what "sent" should mean, so I haven't written this part.

## Before handoff
1. Get the scheduler's trigger (crontab or CronJob) from the current owners. If it's in no repo, the new team inherits a job they can't see.
2. Decide on `/export`: add the route, or delete the module.

## Recommendation
Add a startup or CI test that treats every public function under `handlers/` as a list of what exists. Each one must appear either as a value in `ROUTES` or as a spec in `SCHEDULED_JOBS`, and the test fails otherwise. That test catches today's export case and stays accurate for jobs loaded by name. Also add a test asserting that every scheduled job produces an effect you can check, not just a return value.