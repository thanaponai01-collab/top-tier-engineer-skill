The dashboard now builds in about 0.00s, down from about 6s.

The 2026-10-10 change that moved the flag service config into `fixture/settings.py` introduced a typo in the host name: `flags.internal.exmaple` instead of `flags.internal.example`. That host doesn't resolve, so each flag fetch waited out its 2s timeout. `fetch_flags` retries 3 times (`FLAGS_RETRIES = 3`), which gives 3 × 2s = 6s. It then silently fell back to the default flags, so nothing showed an error.

I corrected the spelling in `settings.py` and re-ran `python dashboard.py`, which printed `1011 bytes in 0.00s`.

Two things I left alone:
- **Fallback to defaults:** a failed flag lookup still returns the default flags without any warning. A log line there would have shown this problem straight away. I can add one if you want.
- **Widget sort:** the selection sort in `dashboard.py` is quadratic, but at 50 widgets it's negligible and isn't the cause.