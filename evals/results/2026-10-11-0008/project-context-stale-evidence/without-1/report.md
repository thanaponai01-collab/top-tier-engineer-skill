**Login is not currently verified.** A login check passed, but only on an older implementation, before the latest expiry change. No current verification record exists.

**Evidence (I only read the records, as asked):**
- `fixture/BUILD.md:2` says the login check predates the latest expiry change and is "historical evidence, not current verification."
- `fixture/work/auth.md:6` says "Session expiry remains unverified" and that there is "no current receipt."
- `fixture/BRIEF.md:2` sets two requirements: preserve login return URLs, and make sure expiring sessions never bypass authentication.

**Unfinished:**
- Session expiry hasn't been verified against the current code.
- Return-URL retention hasn't been verified against the current code.
- Neither requirement from the brief has a current check.

**Next step** (from `fixture/BUILD.md:3-4`): verify session expiry and retained return URLs before extending authentication. Concretely:
1. Check that an expired session redirects to login and never reaches protected content.
2. Check that the original return URL survives that redirect and the login that follows.
3. Record the result in `work/auth.md` as a current receipt.

Don't build further auth features until those checks pass. Because of the expiry change, the old login result shouldn't be trusted either.