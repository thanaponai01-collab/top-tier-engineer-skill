The code still allows up to 1,000 rows, but the owner's current limit is 500, and the boundary test fails today.

**Current constraint.** The owner decided on 2026-10-12 that an export can have at most 500 rows. Anything larger must be rejected, and streaming is not yet approved (`brief/export.md:2-4`). The code hasn't caught up: `app.py:2` is still `return 0 <= rows <= 1000`.

**History** (from git):
- `53bcdc6` (2026-10-09) added `export_allowed`, which only checked `rows >= 0`.
- `df19a71` (2026-10-10), "Bound exports after memory pressure", added the 1,000-row cap.
- `fd8278d` (2026-10-12) recorded the new 500-row decision and added the current `test_limits.py`. It didn't change `app.py`.

**Unfinished work** (`BUILD.md` Next, `work/export.md:4-5`):
- Change acceptance to the 500-row limit. This is done when the boundary check passes.
- Define the message shown for oversized requests. The wording is still undecided, and the work record says to keep that question open while changing the limit.

**Does the recorded check still hold? No.**
- The receipt (`evidence/export.md`) says two tests passed on 2026-10-10, against the 1,000-row rule and commit `df19a71`. That result is out of date because the limit has changed.
- The current tests weren't in git until `fd8278d`, so the tests that passed on 2026-10-10 can't be recovered from history.
- I ran the recipe from `VERIFY.md` (`python -m unittest test_limits`), which only works locally and writes no data. `test_at_limit` passed. `test_above_limit` failed because `export_allowed(501)` returned `True`. That failure is the gap the change needs to close.

**What to change:** lower the bound in `export_allowed` to 500, then rerun the same test.

**Still unknown:**
- The oversized-request message. No source says what it should be.
- Callers of `export_allowed`. The fixture has none besides the test.

I skipped `brief/payments.md` because it covers payments only. No project files changed: running the test created a `__pycache__/` directory, which I deleted, and `git status` is clean.