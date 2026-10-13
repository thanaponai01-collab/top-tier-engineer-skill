## Export size handling: current context

**The current requirement:** an export may have at most **500 rows**, and anything larger must be rejected. The owner decided this on 2026-10-12. It replaces the earlier 1000-row limit, which was dropped because customers reported memory pressure. Streaming is not yet approved. (`fixture/brief/export.md`)

**What the code does now:** `fixture/app.py:1` still uses the old limit: `return 0 <= rows <= 1000`. There are no uncommitted changes, so this is the committed behaviour.

**History (git):**
- `53bcdc6` (10-09): accepted any row count of zero or more.
- `df19a71` (10-10) "Bound exports after memory pressure": added the 1000-row cap.
- `fd8278d` (10-12): recorded the new 500-row decision and updated `test_limits.py` to check 500 and 501. It did not change `app.py`.

**Unfinished work** (`fixture/BUILD.md` Next, `fixture/work/export.md`):
1. Change export acceptance to the 500-row limit. This is done when the boundary check passes.
2. Decide what message an oversized request gets. The wording is still undecided, and the work notes say to keep that question open while changing the limit.

**The recorded test result no longer holds.** `fixture/evidence/export.md` records two tests passing on 2026-10-10, but that was against the 1000-row requirement at `df19a71`. `VERIFY.md` itself says an old pass doesn't prove today's behaviour.

**Check I ran:** `python -B -m unittest test_limits` from `fixture/`. This is the command in `VERIFY.md`; I added `-B` only so no cache files get written. **1 of 2 tests failed:** `test_above_limit` expected 501 rows to be rejected, but `export_allowed(501)` returned `True`. `test_at_limit` (500 rows) passed. The failure matches the gap above: the tests use the new limit and the code still uses the old one. Project files are unchanged, and `git status` shows nothing modified.

**Still unknown:**
- The wording for the rejection message.
- Who calls `export_allowed`. Nothing in `fixture/` does, so I couldn't see how rejections reach users.
- I skipped `brief/payments.md` because it isn't related to exports.

**Next step:** change the limit in `app.py` to 500, rerun the check until both tests pass, and leave the message question open for the owner.