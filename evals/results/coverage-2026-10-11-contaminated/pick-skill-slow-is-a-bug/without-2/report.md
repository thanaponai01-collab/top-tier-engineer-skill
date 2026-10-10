The dashboard is fast again: it now renders in 0.00s, down from about 6s. I ran `python dashboard.py` after the fix to confirm.

**Cause:** on 2026-10-10 the flag service URL moved into `fixture/settings.py`, and it picked up a typo. It read `flags.internal.exmaple` instead of `flags.internal.example`. That host never answers, so each of the 3 retries waited out its 2s timeout before the code fell back to the default flags (3 × 2s = 6s). The fallback hid the failure, so nothing errored and the page just got slow.

**Fix:** I corrected the hostname in `settings.py`. That was the only change.

**Side effect:** the page now gets the real flags, so `new_nav` is `true` and you'll see the new navigation. During the slow period you were getting the `classic` default.

**Not changed:** the 20 → 50 widget change on 10-03 is unrelated, even though the selection sort looks like a possible slowdown. It takes well under a millisecond at 50 items.

**Possible follow-up:** a timeout that silently falls back to defaults is what made this hard to spot. Logging a warning in `fetch_flags` when it falls back would catch the next one quickly. I haven't added it.