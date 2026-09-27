# Handover report: `fixture/` service

## What it is
This is a small Python service with two entry points. It has no third-party dependencies, no tests, no deployment or config files, and no README. It's 8 files and 52 lines in total.

| Entry point | Started by | What it does |
|---|---|---|
| `app.py` | Web process | `dispatch(path)` looks up `path` in `routes.ROUTES`, calls the handler, or returns `(404, "not found")` |
| `scheduler.py` | Cron | `run_all()` reads `settings.SCHEDULED_JOBS` and runs each `"module:function"` spec using `importlib` |

I ran both. `python3 app.py` returns `(200, 'ok')`, and `scheduler.run_all()` completes without errors.

## Live and dead code
The next team needs to get this right before they delete anything. Searching the code for imports gives the wrong answer on both handler files below.

| Module | Status | Why |
|---|---|---|
| `handlers/health.py` | **Live (web)** | It's the only entry in `ROUTES` (`/health`) |
| `handlers/digest.py` | **Live (cron)** | No import statement mentions it, but `settings.py:3` names it as `"handlers.digest:run"` and the scheduler loads it at runtime. **Don't delete it because nothing imports it.** |
| `handlers/export.py` | **Unreachable** | `handlers/__init__.py:2` imports it and its docstring says "Complete, and loaded at startup". But it isn't in `ROUTES` or `SCHEDULED_JOBS`. I checked: `dispatch('/export')` returns 404. Loading it at startup doesn't make it reachable. |

**Decision the new team needs to make about `export.py`:** either add a route for it (for example `"/export": export.run` in `routes.py`) or delete it and remove it from `handlers/__init__.py`. Someone should ask the current owners whether a CSV export was ever meant to ship. The code is finished, so it was probably left unwired by mistake rather than never needed.

## Risks and gaps
1. **Job references are plain strings.** If someone renames or moves `handlers/digest.py` or its `run` function, the web app keeps working, but the nightly cron fails with `ImportError` or `AttributeError`. IDEs and static analysis won't flag it. Recommendation: add a test that imports every spec in `SCHEDULED_JOBS`.
2. **One failing job stops the rest.** `scheduler.py:8-11` has no `try/except`, so an exception in one job skips every job after it. There's only one job today, but this will bite as soon as a second one is added.
3. **Job results are thrown away.** `digest.run()` returns `(200, "digest sent")`, and the scheduler ignores it. There's no logging or alerting, so a job that quietly does nothing looks the same as one that succeeds.
4. **The digest and the export are stubs.** `digest.run` doesn't send anything; it just returns a string. `export.run` returns a hardcoded CSV row (`1,42`) and doesn't read any data. Make sure the new team knows these are placeholders.
5. **There's no real HTTP server.** `app.py` only calls `dispatch("/health")` once and exits. Whatever actually serves traffic in production (a WSGI wrapper, a framework, etc.) isn't in this code. The new team needs to get that from the current owners.
6. **There are no tests, dependency manifest, CI config, or docs.** Someone also needs to supply the cron schedule for `scheduler.py`, since it isn't in the code.

## Questions to settle before the handover
- Should `/export` be routed or removed?
- What serves the web app in production, and where is the cron schedule defined?
- Are `digest` and `export` meant to become real implementations, and who owns that work?
- Where do logs and alerts for the scheduler go?

## Suggested first tasks for the new team
1. Add a test that resolves every `SCHEDULED_JOBS` spec, plus a test for each route.
2. Wrap each job in `scheduler.run_all` in error handling and log the result.
3. Settle what happens to `export.py`.
4. Write a short README covering both entry points and the note that "no import doesn't mean dead code".