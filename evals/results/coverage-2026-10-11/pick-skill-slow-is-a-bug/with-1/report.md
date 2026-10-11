The dashboard now opens in 0.00s instead of 6.00s.

**Cause:** the 2026-10-10 change that moved the flag service settings into `settings.py` introduced a typo in the URL. `FLAGS_URL` says `flags.internal.exmaple` instead of `example`. That host never answers, so each attempt waits out the 2s timeout. With 3 retries that's 6s, after which the client quietly returns default flags. Nothing errored, so nothing flagged it.

**Proof, both directions:**
- **Original code:** 6.00s.
- **Only the typo fixed (scratch copy):** 0.00s.
- **Only the sort removed, typo kept (scratch copy):** still 6.00s. The selection sort over 50 widgets and the 20→50 widget change on 10-03 were not the cause.

**Fix:** `settings.py` now reads `exmaple` → `example`.

**Regression test:** `fixture/test_dashboard_speed.py` has two checks, and both failed before the fix and pass after.
- **Host check:** the configured flags host is one the network shim knows.
- **Speed check:** `render()` finishes in under 1s and shows the real flags (`class=new`), not the defaults.

**Why it wasn't caught:** `fetch_flags` swallows timeouts and falls back to defaults, and no test covered the flag URL. I left that fallback as it is, since changing it is outside what you asked. It's the reason a typo showed up as slowness rather than an error. If you want, I can make the client log a warning when it falls back.

I only used the local test file for the regression check. I didn't run the `verify-loop` handoff.