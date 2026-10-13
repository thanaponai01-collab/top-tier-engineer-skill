**Current constraint:** The owner decided on 2026-10-12 to accept at most 500 rows per export (`brief/export.md`). Larger requests must be rejected, and streaming is not approved. `app.py:export_allowed` still returns `0 <= rows <= 1000`, so it doesn't match that decision.

**History:**
- 2026-10-09, `53bcdc6`: export acceptance started.
- 2026-10-10, `df19a71` "Bound exports after memory pressure": set the limit to 1000 rows.
- 2026-10-12, `abe82eb`: recorded the revised 500-row limit and the pending work. It changed no code, so `app.py` was never updated.

**Unfinished work** (`work/export.md`, `BUILD.md`):
1. Change the acceptance boundary to 500 rows.
2. Define the message shown for an oversized request. The wording is still unresolved, so leave that question open while changing the boundary.

**Does the recorded verification still hold?** No.
- `evidence/export.md` is a 2026-10-10 receipt of two tests passing against the old 1000-row requirement.
- I ran `python -B -m unittest test_limits` from `fixture/`. `test_at_limit` (500 accepted) passes. `test_above_limit` (501 rejected) fails because 501 is still allowed.
- The tests already encode the 500-row limit. Once `app.py` is fixed, the existing tests should be the completion check.

**Left alone:** `brief/payments.md`, `src/billing/reconcile.py` and `work/unrelated/*` have nothing to do with exports. I changed no files; I ran Python with `-B` so it wouldn't write bytecode.