**Wire-check report: `fixture/`, whole-system mode**

**First break:** `handlers/export.py` is not routed, so nothing can reach it. `/export` returns 404 (proven). `handlers/digest.py` is served by the cron job, but only through a string lookup in `settings.py`.

I made no changes. Per the skill, connecting or deleting anything is your call.

**Ways in.** I found two entry points, `app.py` (web, routed through `ROUTES`) and `scheduler.py` (cron, driven by `settings.SCHEDULED_JOBS`). I found no CLI, message consumer or build step in the tree. The deployment itself is outside the tree, so how `scheduler.py` is invoked (crontab or similar) is unverified.

**Inventory vs served set.** The inventory comes from listing the source files: `health`, `export`, `digest`. The served set comes from walking forward from the two entry points.

| Component | Surface | Status | First broken link | Evidence | Proposed outcome |
|---|---|---|---|---|---|
| `health.check` | web `/health` | **Served** | none | proven: `python app.py` prints `(200, 'ok')` | none |
| `digest.run` | cron | **Served, but UNKNOWN to static analysis** | none found; only the cron trigger is outside the tree | proven: `scheduler.run_all()` loaded `handlers.digest` and ran it without error. The return value is discarded. | Add a test that runs `scheduler.run_all()` and checks `digest` ran. Confirm the cron job exists in deployment. |
| `export.run` | web | **Orphaned** | 3, Routed: no entry in `ROUTES` | proven: `dispatch('/export')` returns `(404, 'not found')` | Owner decision: wire it or delete it |

- **`export`:** `handlers/__init__.py:2` imports it, which loads it at startup (link 2 holds). The module imports, but no route triggers it. The "loaded at startup" comment is misleading, because loading is not routing.
- **`digest` return value:** `scheduler.py:11` drops the `(200, "digest sent")` result. If `run()` ever fails by returning an error code instead of raising, nothing notices. This is a link-5 risk, suspected only.
- **`digest` import:** the module is not imported anywhere in the tree. The scheduler loads it by name at run time, so import-based dead-code tools will wrongly flag it as dead. Do not delete it.
- **Counts:** 1 served, 1 served only through a dynamic lookup (UNKNOWN to static tools), 1 orphaned. I am not reporting "all served".

**Connecting code**, only if `export` should be live. This is not applied:

```python
# routes.py
from handlers import export, health

ROUTES = {
    "/health": health.check,
    "/export": export.run,
}
```

If `export` should not be live, delete `handlers/export.py` and its import in `handlers/__init__.py`.

**Recommendation:** add one test that fires every real trigger and checks the effect. For each route in the intended list it would call `app.dispatch(path)` and assert a 200. It would also call `scheduler.run_all()` and assert each `SCHEDULED_JOBS` spec resolves. A module with no route would then fail the test instead of staying silent.

**For the handover:** tell the next team that `export` is unrouted and that `digest` is only reachable through `settings.py`.