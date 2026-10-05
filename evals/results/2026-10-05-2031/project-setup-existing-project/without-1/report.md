The project in `fixture/` is ready for local verification: `python -m unittest discover tests` passes (1 test). That one test is the only check there is.

**What I ran**
- **Baseline:** the test run passed before any change.
- **Setup edits:**
  - `VERIFY.md`: added a Run section and a Feature coverage section.
  - `FEATURES.md`: created, mapping the checkout total to its test.
  - `AGENTS.md`: appended a marked pointer block to `VERIFY.md` and `FEATURES.md`.
- **Validation:** the test passes on the real code. On a temp copy with the fee changed from 10 to 11 it failed, so the check can detect a change. The real `app.py` was not touched.
- **Setup re-run:** I checked rather than re-applied, because every item was already present. The pointer block and Run section each appear once, and the file hashes are identical before and after. Nothing was duplicated or overwritten.

**What stayed as it was**
- `app.py`, `SPEC.md` and the test are unchanged.
- The `MANUAL:` notes in `AGENTS.md` and the live-gateway blind spot in `VERIFY.md` are intact.
- There is no CI, deployment or commit. The folder isn't a git repository anyway.

**Coverage limits**
- Only `total()` is tested, with a single value (100 → 110).
- Nothing tests zero, negative or non-integer input, so the "integer cents" rule in `AGENTS.md` is not enforced by any check.
- The live payment gateway stays a manual blind spot.
- I made no `CLAUDE.md`; the pointer went into `AGENTS.md`, since that is the instructions file the project already has.

<!-- file written by the agent: fixture/FEATURES.md -->
# Features

| Feature | How to reach it | Check |
|---|---|---|
| Checkout total: price in integer cents + fixed 10-cent fee | `from app import total; total(100)` -> 110 | `tests/test_total.py::test_fee` |
