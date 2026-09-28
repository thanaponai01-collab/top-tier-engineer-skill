# Handover report: `fixture/`

## What it is

This is a small Python service of about 52 lines across 8 files. It has no dependencies, no tests, no README and no packaging or deploy config. It is not in a git repo, so there's no history to look back through.

It has **two separate entry points**, and the incoming team needs to know about both:

| Entry point | How it runs | What it reaches |
|---|---|---|
| `app.py` (web) | `dispatch(path)` looks the path up in `routes.ROUTES` and returns `(status, body)` | `/health` → `handlers/health.py:check`, which returns `(200, "ok")` |
| `scheduler.py` (cron) | `run_all()` goes through `settings.SCHEDULED_JOBS` and loads each one with `importlib` | `handlers.digest:run`, which returns `(200, "digest sent")` |

I ran both. `python3 app.py` prints `(200, 'ok')`. `python3 scheduler.py` calls `digest.run` once, which I confirmed by patching the function and counting calls.

## Things the new team could get wrong

1. **`handlers/digest.py` is live even though nothing imports it.** It is never named in an `import` statement. A grep for imports, an IDE's "find usages" or a dead-code tool will all report it as unused. It actually runs through a string in `settings.py:3` (`"handlers.digest:run"`), which `scheduler.py:10` loads at runtime. Deleting or renaming it would break the nightly cron job with nothing warning you beforehand. The same applies to any function named in `SCHEDULED_JOBS`.

2. **`handlers/export.py` looks live but can't be reached.** It gets imported at startup through `handlers/__init__.py:2`, and its docstring says "Complete, and loaded at startup." But no route points to it and no scheduled job names it. I checked: `dispatch("/export")` returns `(404, 'not found')`. Nobody can currently use the CSV export. The owners need to say whether it's meant to be exposed (add a route in `routes.py`) or can be removed. Either way, the new team shouldn't assume it's in production use just because it gets loaded.

3. **Only the code decides what's reachable.** `routes.py` says "Every request reaches a handler through this dict", which is true for web traffic. The cron path skips it completely, so a list of routes is not a full list of live code.

## Gaps and risks

- **No real server.** `app.py` only defines `dispatch()`, and its `__main__` block runs a hard-coded check against `/health`. Whatever actually serves HTTP in production (WSGI wrapper, framework, container) isn't in this directory. Ask the current team where it lives.
- **No cron config.** Nothing here shows when `scheduler.py` runs ("nightly" is only mentioned in a docstring), where it runs, or who gets alerted if it fails.
- **The scheduler stops at the first failure.** `run_all()` doesn't catch errors, so if one job raises, the jobs after it don't run. A malformed entry in `SCHEDULED_JOBS` (missing `:`, typo in the module name) only shows up at runtime.
- **The handlers are placeholders.** `export.run` returns a hard-coded CSV row, `digest.run` doesn't actually send anything, and neither uses any data source or config. Either this is a stub or the real logic lives somewhere else. Confirm which before the handover.
- **No tests, logging or error handling** anywhere.

## Questions to settle before next week

1. Where is the production HTTP server and deploy config, and where is the cron schedule defined?
2. Is `/export` supposed to be live? If yes, add the route. If no, delete `export.py` and remove it from `handlers/__init__.py`.
3. Is `digest.run` a stub? If so, where is the real code that sends the digest?
4. Who gets alerted when the scheduled job fails?

## Suggested cheap fixes before handover

- Put a comment in `handlers/digest.py` saying it's called through `settings.SCHEDULED_JOBS`, and add a test that loads every `SCHEDULED_JOBS` entry so a rename fails loudly.
- Fix the misleading "loaded at startup" docstring in `export.py`, or add the route.
- Add a short README listing both entry points.

I didn't change any code.