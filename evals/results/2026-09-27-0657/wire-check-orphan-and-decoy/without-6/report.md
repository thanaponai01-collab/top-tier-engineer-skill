# Handover report: `fixture/` service

## What it is
A small Python service, 7 files and about 50 lines, with no external dependencies. It has two entry points:

| Entry point | How it runs | What it reaches |
|---|---|---|
| `app.py` | Web process. `dispatch(path)` looks up `routes.ROUTES` | `/health` → `handlers/health.check` → `(200, "ok")` |
| `scheduler.py` | Cron. `run_all()` imports each job listed in `settings.SCHEDULED_JOBS` at runtime | `handlers.digest:run` → `(200, "digest sent")` |

I ran both. `python3 app.py` printed `(200, 'ok')` and `python3 scheduler.py` exited cleanly.

## Things the new team must know

1. **`handlers/digest.py` is live, even though nothing imports it.** The scheduler loads it by the string `"handlers.digest:run"` in `settings.py:3`. A grep for imports or an "unused code" tool will flag it as dead, and deleting it would break the nightly cron. Renaming it would too. Anyone who renames or moves a job must update `SCHEDULED_JOBS`.

2. **`handlers/export.py` looks live but can't be reached.** Its docstring says "Complete, and loaded at startup", and `handlers/__init__.py:2` does import it. But it isn't in `ROUTES`, so no request can get to it. I checked: `dispatch("/export")` returns `(404, 'not found')`. It is effectively dead code. The team needs to decide whether to wire it up (add `"/export": export.run` to `routes.py`) or delete it. The docstring and the `__init__` comment are misleading either way.

3. **The route table is the only way in.** `routes.py` is the single source of truth for web endpoints, and right now it has just one: `/health`.

## Risks and gaps
- **Scheduler results are thrown away.** `scheduler.py:11` calls each job and ignores what it returns. A job that returns an error status would look like a success. An exception in one job also stops every job after it, because there is no per-job error handling.
- **Bad job specs only fail when cron runs.** A typo in `SCHEDULED_JOBS` raises `ImportError` or `AttributeError` at run time, not at deploy time. A startup check that resolves every spec would catch this earlier.
- **`digest.run` is a stub.** It returns `"digest sent"` without sending anything. Confirm whether that's intended before the handover.
- **`export.run` returns hardcoded sample data** (`1,42`), not real order totals.
- **No tests, README, dependency manifest, logging or config for deployment and cron scheduling.** How the web process is actually served and where the cron schedule lives are both outside this tree. The receiving team needs to be told where those are.

## Suggested actions before handover
1. Decide what happens to `export.py` (wire it up or delete it) and fix its docstring and the `__init__` comment.
2. Add a comment in `digest.py` saying it's loaded through `settings.SCHEDULED_JOBS`.
3. Make the scheduler check job return values, handle errors per job, and log.
4. Add basic tests: each route in `ROUTES` resolves and returns 200, and each entry in `SCHEDULED_JOBS` imports.
5. Write down where deployment and the cron schedule are configured.