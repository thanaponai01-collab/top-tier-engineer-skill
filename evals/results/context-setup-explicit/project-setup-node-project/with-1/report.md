Local verification for `fixture/` is ready: `run --strict` and `status` end at `VERIFY-STATE: green`. The check covers one behavior: the checkout adds a fixed 10 cent fee (from `SPEC.md`).

**Setup:** Node v24.18.0, CommonJS, no dependencies, working directory `fixture/`. The folder isn't a git repo.

**What I ran**
- `npm test` on the unchanged product passed.
- A challenge mutated `app.js` from `cents + 10` to `cents + 11` in a scratch copy. The test failed with `expected total 110`, which is the declared fail-signal, so the verdict was **caught**.
- `baseline`, `run --strict` and `status` followed, and `status` printed green.
- `context_budget.py --check-handoff` ended with 0 structural gaps, after I fixed my first start-here links to plain `intent:`/`work:` pointers.
- The second setup pass re-ran the challenge, strict run and status with the same results. The SHA-256 hashes of all setup files and the source were identical before and after, so nothing was rewritten.

**Files**
- **Refreshed:** `VERIFY.md` gained a "Checkout fee" section with the test command, the `SPEC.md` oracle, fail-signal and fail-proof. The existing manual blind-spot line is kept verbatim, with two limits added.
- **Created:** `verification/mutation.json`, `BRIEF.md`, `BUILD.md` (with a Next step) and `.gitignore`, which ignores `.verify-state.json` and `.verify-evidence/`.
- **Appended:** one start-here block in `AGENTS.md`, with its existing text preserved, including the integer-cents and gateway notes.
- **Kept unchanged:** `app.js`, `SPEC.md`, `package.json` and `tests/test_total.js`.
- **Not created:** `FEATURES.md`, since there is only one feature. CI was not set up.

**Limits**
- The check uses a single price (100 cents). Zero, negative and non-integer prices are unspecified and unverified.
- The live payment gateway is out of scope.
- The context is partial: `BRIEF.md` lists the edge-price requirements as an open question.
- One caught mutation shows that mistake is detected, not that the feature is fully covered.
- Nothing was committed, pushed or deployed.

**Next step** (also in `BUILD.md`): get the owner's acceptance criteria for edge prices, then add a spec-backed check for each.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

- Job: checkout adds a fixed 10 cent fee to the supplied price (source: SPEC.md).
- Constraint: amounts are integer cents (source: AGENTS.md, MANUAL note).
- Constraint: no CI or deployment setup requested (source: AGENTS.md).
- Open question: behavior for zero, negative or non-integer prices is unspecified.
- Out of scope: live payment gateway.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

State: app.js and its single check exist; local verification recipe in VERIFY.md is strict green.

## Next
Get owner acceptance criteria for edge prices (zero, negative, non-integer), then add a spec-backed check for each.
Done when: VERIFY.md lists the new checks, each with a rejection receipt, and `run --strict` is green.

## Blockers
- Edge-price requirements unknown.
