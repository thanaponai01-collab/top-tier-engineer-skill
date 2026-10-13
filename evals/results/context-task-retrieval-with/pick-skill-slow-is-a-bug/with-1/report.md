Fixed: the dashboard now opens in **0.00s**, down from **6.00s**. The cause was a typo in a hostname.

**What went wrong:** the change logged in `CHANGES.md` on 2026-10-10 moved the flag service settings into `settings.py`, and the URL was mistyped along the way: `flags.internal.exmaple` instead of `example`. That host never answers, so every page open sat through 3 tries × 2s timeout = 6s. It then quietly fell back to the default flags.

That fallback was a second, hidden bug: users were getting the **classic nav instead of the new one** the flag service turns on. Nothing errors when this happens, which is why nobody caught it.

**Proof, in both directions** (only the host spelling changed between runs):
```
https://flags.internal.exmaple/v1/flags: 6.00s nav=classic
https://flags.internal.example/v1/flags: 0.00s nav=new
```

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| The selection sort in `ordered_widgets` (widgets went 20→50) | Ran it 100 times | 0.0055s total | Ruled out |
| The misspelled flags host is timing out | Same render with only the spelling changed | 6.00s → 0.00s, nav classic → new | **Proven** |

**Changes:**
- `fixture/settings.py:2`: corrected `exmaple` → `example`.
- New `fixture/test_dashboard.py`: checks that the flag host is a known host, and that rendering takes under 0.5s, shows the new nav and has all 50 widgets. On the old code it failed both checks (`'flags.internal.exmaple' not found…` and `6.00 not less than 0.5`). After the fix it passes. Run it with `python -m unittest test_dashboard`.

The test only covers this copy's simulated network in `net.py`. Against the real network, the deeper issue remains: if the flag service is unreachable, the page still blocks for up to 6s and falls back to defaults without saying so. A log or metric on that fallback would have caught this immediately. That's worth adding, but it's a separate change, so I haven't made it.