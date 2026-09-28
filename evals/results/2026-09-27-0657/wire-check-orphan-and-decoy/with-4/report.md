**The one real gap: `handlers/export.py` is loaded at startup, but no request can reach it.** `GET /export` returns `(404, 'not found')`. I ran it (proven). The service has two ways in (the web dispatcher and the cron scheduler), and together they reach `health` and `digest` but never `export`.

A second thing matters for the handover. **Nothing in this repo shows who runs `scheduler.py`.** There's no crontab, Procfile or deploy config in `fixture/` or the folder around it. `digest` works when the scheduler runs, but whether the scheduler runs in production depends on something outside the repo. The receiving team needs to be told where that cron entry lives.

## How I built the lists
- **Ways in** (read from the source): `app.py` handles web requests through `ROUTES` in `routes.py`. `scheduler.py` is the cron entry and loads jobs by name from `settings.SCHEDULED_JOBS` at runtime. I found no other kind of entry: no message queue, CLI or build step.
- **Inventory** (every file in `fixture/`, 8 files and 52 lines): `health.check`, `export.run`, `digest.run`, `app.dispatch`, `scheduler.run_all`.
- **Served** (walked forward from the ways in and then run): `/health` → `health.check` returns `(200, 'ok')`. Running the scheduler calls `digest.run` once; I confirmed this by wrapping the function and counting calls.
- **Orphans** = inventory − served = `export.run`.

A plain search for imports gets this backwards. It flags `digest` as dead, because it's only named in a string and no import statement mentions it, and it counts `export` as live, because `handlers/__init__.py` imports it. Running the code shows the opposite.

## Table

| Component | Surface | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Evidence | Status | Proposed outcome |
|---|---|---|---|---|---|---|---|---|---|
| `health.check` | web `/health` | ✅ | ✅ `routes.py:2` | ✅ `routes.py:5` | ✅ | ✅ `(200,'ok')` | proven | served | none |
| `export.run` | none | ✅ | ✅ imported in `handlers/__init__.py:2` | ❌ **no `ROUTES` entry** | ⛔ | ⛔ | proven (404) | **orphaned** | **Owner decides:** add the route, or confirm it's dead and delete it |
| `digest.run` | cron | ✅ | ✅ loaded by name from the `settings.py:3` string | ✅ `scheduler.py:10-11` | ✅ when the scheduler runs | ⚠️ return value is dropped by `scheduler.py:11` | proven from the scheduler down; what triggers the scheduler is **UNKNOWN** | served, depends on an outside trigger | Record where the cron job is configured |
| `scheduler.run_all` | cron entry | ✅ | n/a | ❓ no trigger in the repo | ❓ | ✅ runs, exit 0 | proven when run by hand | **unknown** | Find the crontab or deploy config and add it to the handover notes |

**Why `export` was missed:** `handlers/__init__.py` imports it with the comment "so both handler modules load". That makes it look wired, but in this system loading a module doesn't route it. Only an entry in `ROUTES` does.

**A side note on `digest`, suspected only:** `run()` returns `"digest sent"` but doesn't send anything, and `run_all` throws the return value away. If it's meant to send email, it's a stub that looks like it works. If it's a placeholder, say so in the handover.

## The connecting code (not applied)
You didn't ask me to change anything, so I haven't. If `/export` is meant to be live, this is the whole fix:

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

After the change, `python3 -c "import app; print(app.dispatch('/export'))"` should return `(200, 'id,total\n1,42')`. If `/export` isn't meant to be live, delete `handlers/export.py` and remove its name from `handlers/__init__.py`.

## Recommendation
Add a test that walks from the entry points: every public handler function in `handlers/` must appear either as a value in `ROUTES` or as a job in `SCHEDULED_JOBS`, and it should fail with the names that appear in neither. That would have caught `export` and can't be fooled by the import in `__init__.py`. Also put the cron schedule in the repo, or link to it, so the scheduler's trigger stops being unknown.