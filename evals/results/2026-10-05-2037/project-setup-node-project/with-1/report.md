**Local verification is ready.** `run --strict` and `status` are green, but only for one claim: the checkout adds a fixed 10-cent fee, checked with 100 → 110.

**Project:** `fixture/`, Node v22.16.0, CommonJS, no dependencies and no lockfile. Every command ran from that folder.

**Files**
- **Created:** `verification/mutation-total.json` (the mutation `cents + 10` → `cents - 10`), `.gitignore` (ignores `.verify-state.json` and `.verify-evidence/`), and `.verify-state.json` (local evidence).
- **Refreshed:**
  - `VERIFY.md` now has a "Checkout total" feature with the test command, `oracle: SPEC.md`, `fail-signal: expected total 110` and a fail-proof note. Your MANUAL gateway blind spot is kept, and I added one more blind spot (below).
  - `AGENTS.md` gained one "Project checks" block. Your MANUAL line and the other instructions are untouched.
- **Kept unchanged:** `SPEC.md`, `app.js`, `package.json` and `tests/test_total.js`. The hashes match the ones I took before any edits, so product behavior and the existing check were not touched.

**Executed**
- `npm test` passed on the original code.
- `verify.py challenge . --feature "Checkout total" --mutation verification/mutation-total.json` came back **caught**. The mutated copy produced 90 against the expected 110 and failed with exit 1, while the original passed.
- `verify.py baseline .`, then `verify.py run . --strict` (green) and `verify.py status .` (`VERIFY-STATE: green`).
- **Second setup pass:** I re-read the specification, manifest, entry point and recipe, and nothing had changed. I re-ran strict and status, which stayed green, and the `VERIFY.md` and `AGENTS.md` hashes matched. There was only one "Project checks" block and one MANUAL line in each file.

**Coverage limits**
- Only the 100 → 110 example is checked. Other amounts and non-integer input are unverified. The test file has one assertion, so I did not add checks of my own.
- The live payment gateway is out of scope (your existing note).
- I did not create `FEATURES.md`, so there is no feature map. Nothing else in the project needed one.
- There is no CI, commit, push or deploy, as you asked.
- This folder isn't a git repository, so the `.gitignore` entries only take effect once it becomes one.
- The state file only shows that checks ran. It doesn't protect against someone editing it.

**Next step:** add a spec-backed second example, such as 0 → 10. You'd need to approve the new expectation and re-run the baseline.