The return-URL change is now recorded in the context documents. The second upkeep pass found nothing more to edit.

**What changed**
- `work/auth.md`: login now keeps its return URL through the shared helper. Session expiry is still marked unfinished, and the check is still marked not run.
- `work/redirect.md`: the helper now returns its target instead of always `/`. The callers that rely on it are login and checkout.
- `BUILD.md`: the login fix is marked done with no checks run. The next step is now session expiry.

**One side effect**
Checkout passes `/billing`, so it now redirects there instead of to `/`. I recorded that in `work/redirect.md`. I left `work/billing.md` alone because its invoice-rounding item is unrelated.

I did not change `BRIEF.md`, `AGENTS.md`, `docs/architecture.md` or any source file.

**Next step**
Implement session expiry so expired sessions can't bypass authentication, then run `tests/test_navigation.py`. That test has not been run.