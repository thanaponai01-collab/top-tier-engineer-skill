Login now keeps its return URL through the shared redirect helper, and the project memory says so. No tests ran, so the change is unverified.

**Updated**
- `work/redirect.md`: the helper now returns the target it is given. It used to always return `/`.
- `work/auth.md`: login keeps its return URL. Session expiry is still marked unfinished.
- `BUILD.md`: records login as done and unverified, and session expiry as unfinished. It has one Next: implement session expiry, then run `tests/test_navigation.py` and add an expiry test.

**Left alone**
- `BRIEF.md` (the owner's requirements) is unchanged.
- `work/billing.md` is unrelated and unchanged. Its invoice rounding question is still open and needs an owner decision.
- `docs/architecture.md` is unchanged, because no boundaries or wiring changed.

**Upkeep**
- Index and check ran once on the three changed documents. The check found no issues, but it only covers structure, not whether the code is correct.
- I captured the Markdown bytes with the probe, repeated index and check on the same paths, and compared. The second pass changed no context documents.

**Gaps**
- The change range was only the before/after described in `CHANGE.md`, not a real diff.
- Checkout calls the same helper and passes `/billing`, so its result changes from `/` to `/billing`. I noted this in `work/redirect.md`. The memory has no record of the owner wanting that, so confirm it is intended.