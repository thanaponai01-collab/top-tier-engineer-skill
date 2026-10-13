The code still allows up to 1000 rows, but the owner lowered the limit to 500. The 2026-10-10 pass no longer holds: the boundary check fails today.

**Current constraint**
- On 2026-10-12 the owner set the limit to **at most 500 rows per export** and said larger requests must be rejected. This replaced the earlier 1000-row limit after customers reported memory pressure. Streaming is **not yet approved** (`brief/export.md`).
- The code still uses the old limit: `app.py:2` has `return 0 <= rows <= 1000`. The entry point is `app.py:export_allowed` (`FEATURES.md`).

**History (git)**
- `df19a71` (2026-10-10), "Bound exports after memory pressure": set the cap to 1000 to limit memory use on small customer machines.
- `fd8278d` (2026-10-12): recorded the 500-row decision and the pending work, and added `test_limits.py`. It did not change `app.py`.

**Unfinished work** (`BUILD.md` Next, `work/export.md`)
1. Change acceptance to 500 rows. This is done when the boundary check passes.
2. Decide the wording of the message for oversized requests. It is **still undecided**, and the notes say to keep that question open while changing the limit. I found no wording anywhere in the records.

**Does the recorded check still hold? No.**
- The receipt in `evidence/export.md` says two tests passed on 2026-10-10, but against the 1000-row requirement. `VERIFY.md` says a past pass doesn't prove today's behaviour.
- The test file in the repo now was only committed in `fd8278d`, after that receipt. So git doesn't contain the test file that run used.
- **I ran the check today** from `fixture/`: `python -B -m unittest test_limits` (the recipe in `VERIFY.md`; `-B` stops Python writing cache files).
  - `test_at_limit` (500 rows) passes.
  - `test_above_limit` fails: `export_allowed(501)` returns True.
  - The run ended `FAILED (failures=1)`, which matches the gap between the code and the 500-row limit.
- `git status` was clean before and after, so no project files changed.

I skipped `brief/payments.md` because it only covers payment reconciliation.

**Next step:** change the bound in `app.py` to 500 and run the check again until it passes. Keep the message wording as an open question for the owner.