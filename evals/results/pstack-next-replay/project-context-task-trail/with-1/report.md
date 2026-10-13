**The recorded verification no longer holds.** `python -m unittest test_limits` currently fails: `test_above_limit` gets `True` for 501 rows.

**Current constraint**
- The owner decided on 2026-10-12 to accept at most 500 rows per export. Larger requests must be rejected. This replaces the earlier 1000-row limit, which was set after memory pressure (`brief/export.md`).
- Streaming is not yet approved (`brief/export.md`).
- `app.py:1` still has `0 <= rows <= 1000`, so the code lags the decision.

**History**
- Three commits: `53bcdc6` (2026-10-09) started export acceptance. `df19a71` (2026-10-10) bound exports after memory pressure. `abe82eb` (2026-10-12) recorded the revised limit and the pending boundary work.
- I read the commit titles only, not the patches.
- `test_limits.py` already expects 500 as the limit. It was updated ahead of the code.

**Unfinished work** (`BUILD.md`, `work/export.md`)
- Update acceptance to 500 rows.
- Define the oversized-request message. The wording is unresolved, so keep it open when you change the boundary.

**Verification**
- `evidence/export.md` records two tests passing on 2026-10-10 against the 1000-row requirement. That receipt is stale and only covers the old limit.
- I ran the command from `VERIFY.md`. It ran 2 tests: `test_at_limit` passes and `test_above_limit` fails.
- A first run with `python -I` failed to import the test module, because `-I` drops the current directory from the import path. Ignore that run.

**Shared caller**
- `src/billing/reconcile.py:batch_allowed` calls `export_allowed`, so billing jobs share this boundary. `FEATURES.md` doesn't list this caller.
- `brief/payments.md` is scoped to payment reconciliation. I did not open it, so check whether a 500 cap affects billing batches.

**Cleanup**
- I removed the `__pycache__` that my test run created. The working tree is clean.