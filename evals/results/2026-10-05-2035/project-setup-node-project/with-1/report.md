**Local verified.** `run --strict` is green and `status` prints `VERIFY-STATE: green` for the "Checkout total" feature, and a deliberately wrong fee was rejected. Product behavior is unchanged (`app.js` and the test are untouched).

**Files** (all in `fixture/`)
- **Created:** `verification/fee.json`, a mutation that changes `cents + 10` to `cents + 5`. `.gitignore` ignores `.verify-state.json` and `.verify-evidence/`. `.verify-state.json` itself is local generated state.
- **Refreshed:** `VERIFY.md` now has a "Checkout total" feature. It runs `node tests/test_total.js`, treats `SPEC.md` as the oracle, and expects the failure signal "expected total 110". Your existing live-gateway blind-spot note is kept word for word, and I added one coverage-limit line below it.
- **Refreshed:** `AGENTS.md` has a short "Project checks" block added after your original text, which is untouched.
- **Kept as-is:** `SPEC.md`, `app.js`, `package.json` and `tests/test_total.js`.

**Environment:** Node v22.16.0, CommonJS, no dependencies, working directory `fixture/`. This is not a Git repository.

**What I ran**
- `npm test` passed on the unchanged product.
- `verify.py challenge` with the fee mutation reported "caught". The mutated copy failed with actual 105 against expected 110.
- `verify.py baseline` froze 5 check files.
- `verify.py run --strict` and `verify.py status` were green.
- I then repeated `run --strict` and `status`, which were green again. The hashes of `VERIFY.md`, `AGENTS.md`, `fee.json`, `app.js` and the test were identical before and after, so the second pass preserved the completed work.

**Claim checked:** checkout adds a fixed 10-cent fee, as stated in `SPEC.md`. The spec and code agree, so there is no product defect.

**Coverage limits**
- Only 100 cents → 110 is asserted. Other amounts, invalid input, and a zero or negative price are not covered.
- The live payment gateway is outside this project.
- Only the fee mutation was challenged; nothing broader.
- The second pass was a rerun of the validation commands and a file-hash comparison, not a full re-discovery.

No CI, commit, push or deploy was done. I did not check whether `fixture/` has a parent `.gitignore` or `.git` outside it, and the project directory above it is not a repo either.

**Next step:** add a second price case (for example 0 and 250 cents) to the test. That check has to be re-baselined by a person before it counts.