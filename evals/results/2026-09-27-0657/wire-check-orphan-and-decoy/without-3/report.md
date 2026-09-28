# Handover report: `fixture/`

## What it is
This is a small Python service, 52 lines across 8 files, with no dependencies beyond the standard library. It has two entry points, and both ran cleanly when I tried them.

| Entry point | How it runs | What it reaches |
|---|---|---|
| `app.py` (web) | `python3 app.py` | `dispatch(path)` → `ROUTES` in `routes.py` → `/health` → `handlers/health.py` → `(200, "ok")` |
| `scheduler.py` (cron) | `python3 scheduler.py` | Reads `SCHEDULED_JOBS` in `settings.py` → `handlers.digest:run` → `(200, "digest sent")` |

## Traps for the new team

**1. `handlers/digest.py` is live, even though nothing imports it.**
Searching for imports won't find it: `scheduler.py:10` loads it by name using `importlib`, based on a string in `settings.py:3`. It is the nightly digest job. **Do not delete or rename it as "unused".** If you rename the module or its `run` function, you must also update `settings.py`. Nothing checks this until cron runs and fails.

**2. `handlers/export.py` is loaded at startup but can't be reached.**
`handlers/__init__.py:2` imports it, and its docstring says "Complete, and loaded at startup". But it has no route in `routes.py` and no entry in `SCHEDULED_JOBS`, so no request or job can ever call it. The import makes it look used when it isn't. Before handover, someone needs to decide:
- whether the CSV export was meant to ship. If so, add a route (e.g. `"/export": export.run`).
- or whether it was abandoned. If so, delete the file and its import.

Also note it returns hardcoded placeholder data (`"1,42"`), so it isn't really finished.

**3. The route table is the only way requests reach code.**
Whether a handler can be reached depends on `routes.py` and `settings.py`, not on imports. Anyone checking what is in use should look at those two files.

## Weak points worth knowing
- **The scheduler has no error handling** (`scheduler.py:7-11`). If one job raises an exception, every job after it is skipped. A spec without a `:` crashes with a `ValueError`, and a typo'd module name crashes with `ModuleNotFoundError`. There is no logging.
- **The scheduler throws away job results.** It ignores the `(status, body)` tuple returned by `digest.run()`, so a failure status would go unnoticed.
- **`digest.run()` is a stub.** It returns `"digest sent"` without sending anything. Find out whether the real sending logic lives somewhere else or was never written.
- **`app.py` isn't a real server.** Run directly, it just dispatches `/health` once and prints the result. Whatever actually serves HTTP in production (a WSGI or framework wrapper) is not in this tree. The new team needs to know where that lives and how it's deployed.
- **The cron schedule isn't in the repo.** Nothing here says when or how often `scheduler.py` runs.
- **There are no tests, no dependency file, no README, and no config for different environments.**

## Suggested handover checklist
1. Decide whether `export.py` gets routed or deleted.
2. Confirm whether `digest.run` really sends anything.
3. Write down where the production HTTP server and the cron schedule are defined.
4. Put a try/except and logging around each job in `scheduler.run_all`.
5. Add a startup check that every entry in `SCHEDULED_JOBS` can be imported. This would catch rename breakage early.
6. Add basic tests for `dispatch` (a known route and a 404) and for each scheduled job.