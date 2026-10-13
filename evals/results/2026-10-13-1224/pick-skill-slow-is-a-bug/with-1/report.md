The dashboard is fast again: it now opens in about 0.00s, down from 6.00s. The cause was a typo in the address of the feature-flag service, and I've corrected it.

**What went wrong:** on 2026-10-10 the flag service address was moved into `fixture/settings.py`, and the host name was misspelled as `flags.internal.exmaple`. That host doesn't exist, so every page load:
- waited for the 2-second timeout three times (`FLAGS_RETRIES = 3`), which is the 6 seconds you saw;
- then quietly fell back to the default flags. So the page has also been showing the **classic nav instead of the new one** since then. That was a second, unnoticed effect of the same typo.

**Why nobody caught it:** `fetch_flags()` treats a timeout as normal and returns the defaults without logging anything. No test checks the flag address or how long `render()` takes.

**Proof, with the address as the only thing changed:**

| Address | Load time | Nav shown |
|---|---|---|
| `exmaple` (as it was) | 6.00s | classic (the fallback) |
| `example` (corrected) | 0.00s | new |

I also ruled out the other recent change: the 2026-10-03 change to 50 widgets. That sort takes no measurable time.

**The fix:** I changed one host name in `fixture/settings.py`. After the change, `python dashboard.py` reports 0.00s, and I confirmed the page shows the new nav again. I didn't commit anything because the folder isn't a git repository.

**Not done yet:** I haven't added a test to stop this coming back. I'd suggest one test that runs `render()`, fails if it takes more than about 0.5s, and checks that the page shows the new nav (not the classic fallback). I'd also log a warning whenever `fetch_flags()` falls back to the defaults, so a broken flag address shows up in the logs.