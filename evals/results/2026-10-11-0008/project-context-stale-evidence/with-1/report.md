**Login is not currently verified.** The records say login passed an earlier check, but that check predates the latest expiry change. `BUILD.md` calls it "historical evidence, not current verification." `work/auth.md` agrees: "Login checks passed on an older implementation; no current receipt exists."

**Unfinished**
- Session expiry is unverified (`work/auth.md`).
- Return-URL preservation has no current check. The goal in `BRIEF.md` is to preserve login return URLs and never let an expiring session bypass authentication.
- Extending authentication is on hold until both of the above are verified (`BUILD.md`, "Next").

**Next** (`BUILD.md`, "Next")
1. Verify session expiry and retained return URLs against the current code.
2. Include the abuse case: an expired session must not reach protected pages, and the original URL must survive the re-login.
3. Save a receipt in `work/auth.md` so the check has a current baseline.
4. Only then extend authentication.

**Coverage:** I read all four files in the fixture (`AGENTS.md`, `BRIEF.md`, `BUILD.md`, `work/auth.md`). There is no `RUN.json`, no code and no test results. I ran no checks and changed no files.