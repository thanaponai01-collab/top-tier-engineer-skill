**Current constraint:** The owner decision of 2026-10-12 (`brief/export.md`) is at most 500 rows per export. Larger requests must be rejected, and streaming is not approved. The code hasn't caught up: `app.py:export_allowed` still returns `0 <= rows <= 1000`.

**History** (from `git log`):
- `53bcdc6` (10-09) started export acceptance.
- `df19a71` (10-10), "Bound exports after memory pressure", set the 1000-row cap.
- `abe82eb` (10-12) recorded the new 500-row limit and the pending work. It also added `test_limits.py`, which already expects 500.

**Unfinished work** (`work/export.md`, `BUILD.md`):
1. Change the acceptance boundary in `app.py` from 1000 to 500.
2. Define the oversized-request message. The wording is still unresolved, so keep it open when you change the boundary and don't invent one.

**Does the recorded verification still hold?** No. `evidence/export.md` and `work/export.md` record a pass on 2026-10-10, but that was against the old 1000-row requirement. I ran `python -B -m unittest test_limits` today, and it gives 1 pass and 1 failure. `test_at_limit` (500) passes. `test_above_limit` fails because `export_allowed(501)` returns True. It will pass once the boundary is 500.

I changed no files. I ran the test with `-B` so it wouldn't write bytecode caches. `brief/payments.md`, `src/billing/` and `work/unrelated/` have nothing to do with this change.