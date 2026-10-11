Login now keeps its return URL through the shared redirect helper. I updated three context files. A second upkeep pass found nothing more to edit.

**Updated**
- `work/auth.md`: login is done. Session expiry is still unfinished and still tied to `BRIEF.md`. The check is marked not run, so the fix is unverified.
- `work/redirect.md`: `preserve(target)` now returns `target` instead of always `/`. I added the caller impact below.
- `BUILD.md`: current work now reflects the change and includes `work/redirect.md`. Next is now "run the navigation tests, then implement session expiry."

**Unchanged on purpose**
- `BRIEF.md` is owner intent, so I left it alone.
- `work/billing.md` still holds the open invoice-rounding decision.
- `docs/architecture.md` is still accurate, because no boundaries or wiring changed.

**Impact beyond login (traced):** `checkout()` calls `preserve('/billing')`. It used to return `/` and now returns `/billing`. No billing record covers this, and nobody has confirmed it is intended. I noted it in `work/redirect.md` rather than inventing a billing record. That is a coverage gap.

**Evidence gaps**
- `CHANGE.md` says no checks ran, and I didn't run any, so nothing is verified. `tests/test_navigation.py` expects `/profile` and `/billing`, which matches the new code.
- There is no git repository, so I had no change range. I relied on the before/after in `CHANGE.md` and read the current callers.
- I didn't run the index/check helper. The fixture has no helper, and I checked links by hand.

**Next:** run `tests/test_navigation.py` and record the result, then implement session expiry. The owner also needs to confirm the `checkout()` behavior change.