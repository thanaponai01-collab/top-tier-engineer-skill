**Current constraint**
- The owner decision of 2026-10-12 (`brief/export.md`) is to accept at most 500 rows per export. It replaces the earlier 1000-row limit because of customer memory pressure.
- Larger requests must be rejected, and streaming is not approved.
- The code still allows 1000 rows: `app.py:export_allowed` returns `0 <= rows <= 1000`. It is out of date.

**History**
- `53bcdc6` (2026-10-09) started export acceptance.
- `df19a71` (2026-10-10), "Bound exports after memory pressure", set the 1000-row bound in `app.py`.
- `abe82eb` (2026-10-12) recorded the new 500-row limit and the pending work. It did not change `app.py`.
- `brief/payments.md` says payments keep a 1000-item batch size. That constraint belongs to payments and has nothing to do with exports.

**Unfinished work** (`work/export.md`, `BUILD.md`)
- Update acceptance to 500.
- Define the oversized-request message. The wording is still unresolved, so keep that question open while you change the boundary.

**Hidden caller**
- `src/billing/reconcile.py:batch_allowed` calls `export_allowed`, and `FEATURES.md` doesn't list it.
- Billing's 1000-item batches would start failing if you lower the shared limit to 500.
- That is a conflict with `brief/payments.md`. Decide whether billing gets its own check before you change `app.py`.

**Does the recorded verification still hold?**
- No. The receipt `evidence/export.md` (2026-10-10) covers only the old 1000-row requirement, and `VERIFY.md` says a historical pass doesn't establish today's behavior.
- I ran `python -m unittest test_limits` from `fixture/`, with bytecode writing off. It ran 2 tests and 1 failed: `test_above_limit` fails because `export_allowed(501)` returns True.
- The test already expects the 500 limit, so the failure is the code lagging the requirement. The tests don't cover the billing caller.

**Coverage**
- I read the startup block, the export and payments records, the code and tests, and the git history. I skipped `work/unrelated/*` because those records say they have no export dependency.
- The working tree is clean and I changed no files. There was no RUN.json and I didn't use the context.py index.