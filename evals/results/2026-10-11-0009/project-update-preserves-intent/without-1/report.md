The context docs now record the return-URL fix as done and session expiry as still unfinished. A second upkeep pass needed no further edits. I only read the source and test files and ran nothing, so the checks are still unrun.

**Edits**
- `work/redirect.md`: the helper now returns its target unchanged. This also changes checkout, which now returns `/billing` instead of `/`, so I recorded that effect.
- `work/auth.md`: login retains its return URL, and session expiry is still open.
- `BUILD.md`: the old "implement return URL" next step is replaced. I also added a link to the redirect record, since its change reaches checkout.

**Left alone:** `BRIEF.md` (the owner requirement), `AGENTS.md`, `docs/architecture.md` (still accurate), and `work/billing.md` (invoice rounding is an open owner decision).

**Second pass:** I searched the markdown for the old wording ("always", "loses", "pending", "Implement return"). The only hit was the intentional "was: always `/`" note in `work/redirect.md`.

**Next step:** run `tests/test_navigation.py`, which covers both callers, then implement session expiry so expired sessions can't bypass authentication.