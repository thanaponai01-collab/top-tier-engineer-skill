**Verdict:** one real orphan. `handlers/export.py` (the CSV export of order totals) is fully written and loads at startup, but no route points to it. Every request for it returns **404**, which I ran and confirmed. There are also two things the repo can't answer, which the receiving team should settle before sign-off. Is `scheduler.py` actually run by any cron? And does the nightly digest have any effect at all? Its only output is a return value that the scheduler throws away.

I changed nothing. The connecting code is below for you to apply if you want it.

## Ways in (counted before the walk)

| Kind | Entry point | Where it's declared | Status |
|---|---|---|---|
| HTTP request | `app.py` → `dispatch(path)` → `routes.ROUTES` | `routes.py:4` | Ran it: `/health` → `(200, 'ok')` |
| Schedule (cron) | `scheduler.py` → `run_all()` → `settings.SCHEDULED_JOBS` | `settings.py:3` | Ran it: exits 0. **What triggers it is outside the repo** (no crontab, Procfile or CI config in the tree) |
| CLI / message / other service / build step | none found | n/a | Searched the tree; nothing else is there |

**Important:** `handlers.digest:run` is only reached through a string loaded with `importlib` (`scheduler.py:10`). No `import` line mentions it anywhere. A plain import-graph tool would wrongly call digest an orphan, and would miss export because `handlers/__init__.py` imports it.

## Inventory vs. served set

I built the inventory by listing every function in the source files. The served set is what I reached by walking forward from the two entry points.

| Component | 1 Exists | 2 Registered | 3 Routed | 4 Invoked | 5 Reachable | Evidence | Result |
|---|---|---|---|---|---|---|---|
| `health.check` | ✅ | ✅ `routes.py:2` | ✅ `/health` | ✅ | ✅ response returned | proven (`python3 app.py` → `(200,'ok')`) | **served** |
| `export.run` | ✅ | ✅ `handlers/__init__.py:2` | ❌ **no `/export` in `ROUTES`** | ⛔ | ⛔ | proven (`dispatch('/export')` → `(404,'not found')`; calling it directly gives CSV) | **orphaned: not routed** |
| `digest.run` | ✅ | ✅ `settings.py:3` (a string, loaded dynamically) | ⚠️ cron trigger is outside the repo | ✅ `run_all()` calls it | ❌ **return value thrown away** (`scheduler.py:11`), and it has no side effect of its own | proven for 2–4 (ran it via the scheduler's own lookup → `(200,'digest sent')`); link 3 unknown; link 5 traced | **unknown / effect lost** |
| `app.dispatch`, `scheduler.run_all` | ✅ | n/a (these are the entry points) | n/a | ✅ | ✅ | proven | served |

Totals: **2 served, 1 orphaned, 1 unknown.** I'm not calling this "all served".

## Findings

**1. Export is built but has no route (first broken link: 3, Routed).**
- **Why it was missed:** it's imported at startup, so it looks connected, but only `routes.py` decides what's reachable.
- **Outcome:** this is the owner's call. Either wire it up (code below) or confirm it's dead and delete it.

**2. The digest's effect is lost (link 5), and its trigger is unknown (link 3).**
- `digest.run()` doesn't send anything. It just returns `(200, "digest sent")`, and `run_all()` ignores whatever the job returns.
- So even if cron runs the job every night, nothing happens anywhere. It is either a stub or a live bug that looks like working code. I've only traced this, not proven it: there's no mail or queue call to watch.
- **Two questions to ask before handoff:** where is the crontab that runs `python3 scheduler.py`, and what is the digest supposed to write or send?

## Connecting code (not applied)

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

To prove it works afterwards: `python3 -c "import app; print(app.dispatch('/export'))"` should print `(200, 'id,total\n1,42')`.

For the digest there's no connecting code I can write. It needs the real send or write call from whoever owns it. After that, `run_all` should at least log or raise on a failed result instead of discarding it.

## Recommendation

Add one test that fails when the inventory and the served set drift apart:
- Every public handler in `handlers/` must appear either in `ROUTES` or, resolved via `importlib`, in `SCHEDULED_JOBS`.
- Anything intentionally unserved must be listed in an explicit allowlist.

Also, move the cron schedule into the repo (a crontab file or deploy config), so the second way in can be seen by the next team rather than living only on a server.