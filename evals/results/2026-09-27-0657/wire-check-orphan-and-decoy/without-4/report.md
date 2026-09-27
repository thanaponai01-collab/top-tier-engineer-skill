# Handover report: `fixture/`

## What it is
A small Python service (8 files, about 50 lines) with **two separate entry points**. It's not a git repo and has no tests, dependency manifest, README, or deploy/cron config.

| Entry point | How it runs | What it reaches |
|---|---|---|
| `app.py` (web) | `dispatch(path)` looks the path up in `routes.ROUTES` | `/health` → `handlers/health.py:check` |
| `scheduler.py` (cron) | `run_all()` imports each `module:func` string in `settings.SCHEDULED_JOBS` at runtime | `handlers.digest:run` |

I ran both: `python3 app.py` printed `(200, 'ok')`. `python3 scheduler.py` printed nothing, because the scheduler throws away job return values. Calling `digest.run()` directly returns `(200, 'digest sent')`.

## What's live and what's dead
- **`handlers/health.py`: live** (web). It's the only route.
- **`handlers/digest.py`: live** (cron), even though no `import` statement mentions it. It's reached only through the string in `settings.py:3`. **Don't delete it because it looks unused.** Grepping for imports misses it, and renaming the module or function will break the nightly job silently until it runs.
- **`handlers/export.py`: dead code.** It gets imported at startup (`handlers/__init__.py:2`), but no route and no scheduled job points to it. The only references are that import and its own docstring. "Loaded at startup" is true; "used" is not. The new team should decide whether to wire it up (e.g. add an `/export` route) or delete it.

## Comments that will mislead the new team
- `app.py:1` says "The process starts here and nowhere else." That's false: `scheduler.py` is a second, independent entry point.
- `routes.py:1` says "Every request reaches a handler through this dict." That's true for web requests, but the cron job skips it entirely.
- `handlers/__init__.py:1` says "so both handler modules load." There are three handler modules, and the one that matters for cron (`digest`) isn't in that import.
- `handlers/export.py:1` calls itself "Complete." It returns hard-coded rows (`"1,42"`), so it's a stub, not a real export of order totals.

## Operational risks
1. **The scheduler has no error handling or logging.** If one job raises an exception, `run_all()` aborts and the jobs after it don't run. Return values (status codes) are discarded, so a failed digest is invisible.
2. **Job specs are only checked when they run.** A typo in `SCHEDULED_JOBS` shows up as an `ImportError` or `AttributeError` at cron time, not at deploy time.
3. **Imports depend on the working directory.** Imports like `from routes import …` and `from settings import …` only work when the process starts from inside `fixture/`. Whatever runs cron and the web process has to set the working directory or `PYTHONPATH`, and that config isn't in this tree.
4. **The digest is a stub.** It returns `"digest sent"` without sending anything. Confirm whether that's intended before the handover.
5. **There's no web server.** `app.py` only defines `dispatch()` and a manual `__main__` check. Whatever actually serves HTTP lives somewhere else and should be identified.

## Suggested actions before handover
- Fix the four misleading comments above.
- Decide what happens to `export.py`: wire it up or delete it.
- Add a startup check that imports every `SCHEDULED_JOBS` entry, and make the scheduler catch and log errors per job.
- Write down where cron and the web process are configured and which working directory they use.
- Add at least smoke tests for `dispatch("/health")` and `scheduler.run_all()`.