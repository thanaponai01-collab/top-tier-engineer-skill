The completed login change is now recorded in project memory. The second upkeep pass found nothing left to edit; the probe's compare step reported the documents unchanged.

**What I changed**
- `work/auth.md`: login now retains its return URL through the shared helper, and session expiry is still marked unfinished.
- `work/redirect.md`: the helper now returns its target instead of always `/`. I also noted a side effect from the current callers: checkout passes `/billing`, so it now returns `/billing` instead of `/`.
- `BUILD.md`: the return URL fix is marked done but unverified, because no checks ran. Session expiry stays open, and the next step is updated.

I left `BRIEF.md`, `work/billing.md`, `docs/architecture.md` and `AGENTS.md` alone. The brief's owner requirement still stands, the invoice rounding item is unrelated, and the architecture and start-here records are still accurate. I didn't touch any source files.

**Next step:** run `tests/test_navigation.py` to verify the return URL change, then implement session expiry so expired sessions cannot bypass authentication.