Project memory now records that login keeps its return URL, and that session expiry is still unfinished. No checks ran, so the change is unverified.

**Updated**
- `work/auth.md`: login now retains the return URL through the shared helper. Session expiry is still unfinished.
- `work/redirect.md`: `preserve(target)` now returns its target instead of always `/`. This also changes checkout, which now returns `/billing` instead of `/`. I recorded that as a side effect of the shared change.
- `BUILD.md`: the current-work summary is updated, and `work/redirect.md` is now included because the shared helper is active work. Next is below.

**Left alone**
- `BRIEF.md` keeps the owner requirements: expired sessions cannot bypass authentication, and login retains its return URL.
- `docs/architecture.md` is unchanged because no boundaries or wiring moved.
- `work/billing.md` keeps its unresolved invoice-rounding item.
- `AGENTS.md` is unchanged.

**Evidence gaps**
- `tests/test_navigation.py` has not been run. It asserts both the new login and the new checkout behaviour. I recorded it as unverified.
- No change range or git history was available (the folder isn't a git repository). I used the before/after in `CHANGE.md` and the current callers.
- The helper script isn't installed, so I edited the Markdown files by hand and did no index or check run.

**Second upkeep pass**
I re-read the records against the sources and they agree, so no further document edits were needed.

**Next:** run `tests/test_navigation.py` to verify the return-URL change, then start session expiry.