Project memory now matches the completed login change. The second upkeep pass needed no further edits. I made no source edits and ran no tests, so this is proven only by reading `redirect.py`, `login.py` and `checkout.py`. This directory isn't a git repository, so I used the before/after in `CHANGE.md` as the change range.

**Updated**
- `BUILD.md`: the login return URL fix is marked done but unchecked, and session expiry stays open. It now includes `work/redirect.md`, which it hadn't listed before.
- `work/auth.md`: login keeps its return URL through `preserve(target)`, and session expiry is still unfinished.
- `work/redirect.md`: `preserve(target)` now returns the target instead of always `/`.
- `docs/architecture.md`: one line noting that `preserve(target)` returns its target unchanged.

**Left alone**
- `BRIEF.md`, the owner requirements.
- `work/billing.md`, where the invoice rounding decision is still open and the tax rules stay as they are.
- `AGENTS.md`.

**Side effect:** checkout passes `/billing`, so it now returns `/billing` instead of `/`. I recorded this in `work/redirect.md` so it isn't a surprise.

The second pass was a search for stale wording ("loses", "always returns", "pending", "Implement return"). It found nothing.

**Next step:** run `tests/test_navigation.py`, then build session expiry, so expired sessions can't bypass authentication.