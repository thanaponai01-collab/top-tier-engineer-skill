**Current constraint:** Exports are capped at **500 rows**, and anything larger must be rejected. The owner decided this on 2026-10-12 (`brief/export.md`), replacing the old 1000-row limit because customers reported memory pressure. Streaming is not approved yet. The 1000-item limit in `brief/payments.md` is for payment batches only and doesn't apply to exports.

**Code today:** `app.py:2` still says `return 0 <= rows <= 1000`, so it accepts 501–1000 rows. The code is behind the requirement.

**History (git):**
- `53bcdc6` (10-09): added `export_allowed` as `rows >= 0`, with no upper limit.
- `df19a71` (10-10) "Bound exports after memory pressure": added the 1000 cap.
- `fd8278d` (10-12): recorded the 500 limit, added the docs and `test_limits.py` (which tests 500/501), and listed the code change as pending work.

**Unfinished work** (`work/export.md`, `BUILD.md`):
1. Change the acceptance check to 500.
2. Decide what message an oversized request gets. The wording is still open, so keep that question open when you change the limit; don't settle it as a side effect.

The task is done when the boundary check passes.

**Does the recorded verification still hold? No.**
- The 10-10 receipt (`evidence/export.md`) recorded a pass against the old 1000-row requirement, and `VERIFY.md` itself says a past pass doesn't prove current behaviour.
- The receipt also can't be reproduced from git: `test_limits.py` was first committed on 10-12, already testing for 500.
- I ran `python -B -m unittest test_limits` from `fixture/` (the check listed in `VERIFY.md`; `-B` stops it writing `.pyc` files). Result: 2 tests ran and 1 failed. `test_at_limit` passed. `test_above_limit` failed: `export_allowed(501)` returned `True`.

The fix is to change `1000` to `500` in `app.py`, then re-run the check and record a new receipt.

No project files were changed and the working tree is clean.