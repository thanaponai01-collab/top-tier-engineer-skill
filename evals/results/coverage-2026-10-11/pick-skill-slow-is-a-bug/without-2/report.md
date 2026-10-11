The dashboard now builds in about 0.00s instead of about 6s.

The cause was a typo in `fixture/settings.py`. The flag service URL said `flags.internal.exmaple` instead of `example`. That typo came in with the 2026-10-10 change that moved the URL into `settings.py`. The hostname never resolved, so each flag fetch waited out its 2s timeout. With 3 retries that comes to 6s, and then the code fell back to the default flags. I fixed the spelling and re-ran `python dashboard.py` to confirm the new time.

Because of that fallback, the page was also quietly using the default flags (`new_nav` off) the whole time. With the URL fixed it gets the real flags, so the nav now renders as "new" rather than "classic".

I left the retry and timeout settings alone. If the flag service is down again, the page will still stall for 6s before it falls back to defaults. Lowering the timeout or retry count would shorten that, if you want it.