# Handover report: `fixture/` service

## What it is
This is a small Python service of about 50 lines. It has no third-party dependencies, no tests, no packaging (no requirements file, Dockerfile, or README) and no git history. It has two entry points, and both must be run from inside `fixture/` because the imports are bare (`from routes import …`).

| Entry point | How it runs | What it reaches |
|---|---|---|
| `app.py` (web) | `dispatch(path)` looks up the path in `ROUTES` (`routes.py:4`) | `/health` → `handlers/health.py` → `(200, "ok")` |
| `scheduler.py` (cron) | Reads strings from `settings.SCHEDULED_JOBS` and resolves them with `importlib` (`scheduler.py:8-11`) | `"handlers.digest:run"` → `handlers/digest.py` |

I ran both. `python3 app.py` prints `(200, 'ok')` and `python3 scheduler.py` exits cleanly.

## Module status

- **`handlers/health.py`**: live, reached through the `/health` route.
- **`handlers/digest.py`**: live, even though no import statement mentions it. The only thing that reaches it is the string `"handlers.digest:run"` in `settings.py:3`. **Do not delete it because "nothing imports it."** Anyone renaming it must also update `settings.py`.
- **`handlers/export.py`**: **unreachable.** It is imported in `handlers/__init__.py:2`, so it loads at startup, but nothing calls `export.run()`. It has no route and no scheduled-job entry. Its docstring says "Complete, and loaded at startup," which is true but misleading: loading the module doesn't mean the CSV export is being served. The receiving team should find out whether someone expects this export to work. Then either add a route (e.g. `"/export": export.run` in `routes.py`) or delete the module.

## Things the new team should know

1. **String-based job wiring.** Scheduled jobs are resolved at runtime from `settings.SCHEDULED_JOBS`. IDE "find usages", linters and dead-code tools won't see those references. A typo or a renamed module only shows up as an `ImportError` or `AttributeError` when cron fires.
2. **Scheduler ignores results and errors.** `run_all()` throws away each job's `(status, body)` return value. It has no try/except, so if one job fails, every job after it is skipped. It also has no logging.
3. **Handlers are stubs.** `digest.run()` just returns `"digest sent"` and sends nothing. `export.run()` returns a hardcoded CSV row. Neither talks to a real data source or mail system. Confirm whether these are placeholders or the intended behaviour.
4. **Stale comment.** `handlers/__init__.py:1` says "both handler modules load," but there are three. `digest` is deliberately not imported there.
5. **No real web server.** `app.py` only calls `dispatch("/health")` once and prints the result. Whatever actually serves HTTP in production isn't in this tree. Ask for it before handover.
6. **No tests, CI or deployment config.** The cron schedule for `scheduler.py` isn't defined here either.

## Suggested handover checklist
- [ ] Decide what happens to `export.py`: add a route or delete it.
- [ ] Get the real HTTP server and cron configuration from the current owners.
- [ ] Confirm whether `digest` and `export` are meant to be real implementations.
- [ ] Add per-job error handling and logging to `scheduler.py`.
- [ ] Add a startup check that every `SCHEDULED_JOBS` entry resolves, so broken specs fail at deploy time instead of at 2 a.m.
- [ ] Fix the comment in `handlers/__init__.py`, and add a README that explains both entry points.