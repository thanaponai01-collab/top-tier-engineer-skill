**Readiness: local verified.** `run --strict` is green and `status` prints `VERIFY-STATE: green`, after the mutation was caught and the baseline was frozen. Coverage is one behavior only.

**Project:** `fixture/` is the project root. It is a Python 3.13.4 library with no manifest and no git repo. It uses stdlib `unittest`.

**Files**
- **Created:**
  - `fixture/verification/fee_mutation.json`
  - `fixture/.gitignore`, which ignores `.verify-state.json`, `.verify-evidence/` and `__pycache__/`
  - `fixture/.verify-state.json`, the generated state file
- **Refreshed:**
  - `fixture/VERIFY.md` gained a `Checkout Fee` section and one blind-spot line.
  - `fixture/AGENTS.md` gained a short "Project checks" pointer.
- **Kept:** `app.py`, `SPEC.md` and `tests/test_total.py` are untouched. The existing manual notes (the integer-cents rule, the live payment gateway blind spot and the no-CI/deploy note) are preserved word for word. I did not create `FEATURES.md`.

**Commands executed**
- `python -m unittest discover tests` on the unchanged product passed.
- `verify.py challenge . --feature "Checkout Fee" --mutation verification/fee_mutation.json`
- `verify.py baseline .`
- `verify.py run . --strict`
- `verify.py status .`
- **Second setup pass:** I re-ran strict, status and challenge, then diffed the files. They were unchanged, apart from the state file, and the second pass was green again.

**Claim:** `SPEC.md` says checkout adds a fixed 10-cent fee, and the check asserts `total(100) == 110`.
**Rejection signal:** the mutation `cents + 10` → `cents + 11` was caught in a scratch copy with `AssertionError: 111 != 110 : expected total 110`.

**Coverage limits**
- Only the fixed fee is mapped.
- The live payment gateway is untested; that blind spot is recorded in `VERIFY.md`.
- The integer-cents rule from `AGENTS.md` has no check of its own.
- `SPEC.md` has no other requirements to verify.
- I did not edit any existing test.
- I did not commit, push, configure CI or deploy.

**Next step:** if you want integer-cents covered, add a requirement to `SPEC.md` and a test for it.