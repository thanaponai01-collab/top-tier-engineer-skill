**Verdict:** one orphan, `handlers/export.py`. It is loaded at startup but no route reaches it, so `/export` returns 404. `digest` is reachable only through the scheduler, and I couldn't prove that anything runs the scheduler. I changed nothing.

## Entry points counted first

| Entry | Instances | Evidence |
|---|---|---|
| Web request | `app.dispatch` → `routes.ROUTES` | read, and run |
| Scheduled job | `scheduler.run_all` → `settings.SCHEDULED_JOBS` | read, and run |
| Whatever invokes `scheduler.py` | **no crontab, CI file or service definition in `fixture/`** | **UNKNOWN** |

## Inventory (from the source) vs. served set (from the entry points)

- **Inventory:** the three handler modules, `health`, `export` and `digest`. I built it from the `Glob` of `fixture/`, not from the walk.
- **Served by the web:** `/health` only (`routes.py:4-6`).
- **Served by the scheduler:** `handlers.digest:run`, resolved by string through `importlib`.

## Report

| Component | Surface | Result | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | First broken link |
|---|---|---|---|---|---|---|---|---|
| `health.check` | web | **served** | ✅ proven | ✅ proven | ✅ proven | ✅ proven | ✅ proven (`200 ok`) | none |
| `export.run` | web | **orphaned** | ✅ proven | ✅ proven (loaded via `handlers/__init__.py`; `handlers.export` in `sys.modules`) | ❌ proven (`dispatch("/export")` → `404`) | ⛔ blocked | ⛔ blocked | link 3: no `ROUTES` entry |
| `digest.run` | cron | **unknown** | ✅ proven | ✅ proven (string spec in `settings.py:3`) | ✅ proven (`scheduler.py` calls it → `200 digest sent`) | ⛔ unknown: nothing in the repo launches `scheduler.py` | ⚠️ see below | link 4, unconfirmed |

Findings:

1. **`export` is loaded but not routed.** The comment in `handlers/__init__.py` ("Imported at startup so both handler modules load") makes it look wired. Loading is link 2, not link 3. `routes.py` imports only `health`, so the route table never learns about `export`. This one is **proven**: I fired the real request and got a 404.
2. **`digest` is invisible to import-based search.** No import statement names it, so a grep-based dead-code sweep would wrongly delete it. It does run when `scheduler.run_all()` runs (proven). Whether anything runs `scheduler.py` in production is **UNKNOWN**, because it would be a crontab or platform schedule outside this tree. Ask the previous owners where it's scheduled.
3. **Possible lost effect in `digest` (link 5, suspected).** `run()` only returns `(200, "digest sent")` and `run_all()` throws the return value away. Nothing here sends a digest or logs one. Either the body is a stub, or the real send lives elsewhere. Check this before handover.

**Unknown count: 1** (the scheduler's external trigger). I'm not reporting "all served".

## Connecting code (proposed, not applied)

If `/export` was meant to be public, change `routes.py`:

```python
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

Check: `cd fixture && python -c "import app; print(app.dispatch('/export'))"` should print `(200, 'id,total\n1,42')` instead of `404`. If `export` was meant to be internal, it's your decision whether to delete it or leave it. Nothing else here calls it. Note that this route would serve order totals with no auth check in this code.

## Recommendation

Add a small test that walks the real triggers, not imports. For every module in `handlers/`, it asserts the module is either a key in `ROUTES` or named in `SCHEDULED_JOBS`, with an explicit allowlist for intentional exceptions. It would have failed on `export`. The `importlib` string spec should also get a test that resolves every `SCHEDULED_JOBS` entry, so a typo fails in CI instead of at 2am.

For the handover, also get the scheduler's real trigger and the intended purpose of `/export` and `digest` written down.