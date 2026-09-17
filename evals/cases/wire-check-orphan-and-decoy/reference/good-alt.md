# What this system serves — fixture/

Same verdict as `good.md`, written by someone else. If the grader only accepts
one of these two, it is grading prose, not findings.

Two entry points exist and both had to be walked before anything could be called
unreached:

- `app.py:12` — the request dispatch, the way in for HTTP.
- `scheduler.py:9` — a cron loop, the second way in. Walk only the first and the
  digest job looks abandoned.

**Served today:** `/health` → `handlers/health.py:4`, and the nightly digest,
reached from `scheduler.py` through the job name held in `settings.py`.

**Reaches nothing:** `handlers/export.py`. It imports cleanly at startup from
`handlers/__init__.py`, which is what makes it look alive, but `routes.py` has no
entry mapping to it — I read every mapping in the table and none names it. Loaded
is not routed. That handler cannot be invoked by any request this process accepts.

`handlers/digest.py` is a different story and must not be filed with it. Nothing
imports it in source either, yet it runs every night: `settings.py` holds its
module path as a plain string and the scheduler resolves that name at run time.
Grep for an import and you will conclude it is unused; that conclusion is wrong,
and acting on it takes out the nightly digest.
