Route: **`debug-protocol`**. It's "slow since yesterday" with an unknown cause, so it's a bug to
diagnose, not a performance job. Started it:

- Reproduced: `python dashboard.py` → `6.01s` [proven].
- Profiled: 6.0 s is inside `flags_client.fetch_flags`, and the widget sort takes 0.1 ms.
- Cause: yesterday's change (CHANGES.md, 2026-10-10) moved the URL into `settings.py` as
  `https://flags.internal.exmaple/...`, a **typo** for `example`. The host never answers, so it's
  3 retries × 2 s timeout, then silent fallback to defaults (classic nav).
- Fix: corrected the host in `settings.py`. Now `python dashboard.py` → `0.00s`, new nav served
  [proven].

The selection sort looks quadratic but it's 50 items and microseconds, so I left it alone.
Separately: the silent fallback hid this for a day. A log line when flags fall back to defaults would have shown it.
