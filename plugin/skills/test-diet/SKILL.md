---
name: test-diet
description: >-
  Make tests shorter to read and faster to run without losing a single bug they catch: find setup copied across tests (the path each replays to reach its state), slow tests and why, and tests that only check mocks; slim them; prove with planted bugs that the slimmer tests still catch everything the old ones did. Use for "my tests are too long", "tests are slow", "clean up the tests", "too much setup in tests".
disable-model-invocation: true
metadata:
  stage: review
  card: "shorter, faster tests that still catch every bug"
---

# Test diet

**Goal:** the tests are shorter and faster, and the user sees it in numbers (lines, tests, seconds,
planted bugs caught, before and after). Nothing the old tests caught is lost, and no app file changes.
`D` is `python <this skill's base directory>/scripts/diet.py <repo>`, run from the repo root.

1. `D [paths] --run "<test cmd>"` before you change anything. Use `python -m unittest ...` or
   `pytest ...` so each test is timed. It records the suite, each test's time, and which planted bugs
   (small changes to the app code the tests import) the suite catches, and lists leads in
   `.diet/candidates.md`:
   - `setup:<id>`: statements repeated across tests, with the calls they replay (`make_user ->
     verify -> pay`). Often many tests walk the same path just to reach the state one of them checks.
     Make a fixture, a builder, or a helper that starts in that state.
   - `slow:<test>`: 0.25 s or more, or a body that sleeps, opens the network or starts a process.
   - `mock:<test>`: every assertion checks a mock. Check a result instead, or delete the test if
     another one already holds the behavior.
2. Slim the tests. Deleting and merging tests is allowed. Change only test files (tests folders,
   `test_*` files, `conftest.py`). A slow test caused by app code is kept, with that reason.
3. Write `.diet/plan.json`: `changes` (`covers`: lead ids, `what`, `at`) and `kept` (`candidate`,
   `why`).
4. `D --done`. It refuses while a lead is neither covered nor kept with a reason, a covered setup is
   still in two or more places, a covered slow test is not at least twice as fast (or under 0.1 s),
   a covered mock-only test still checks only mocks, an app file changed, the tests fail, test lines
   grew, the suite got slower, or a planted bug the old tests caught is now missed. Fix the cause,
   never the check: a missed planted bug means a check you removed was the only one holding that
   code, so put it back. It writes `.diet/REPORT.md` and prints `DIET: done`.

The answer, in plain words: the before and after numbers first, then what changed, what was kept
and why, and what was not checked (run order, flakiness).
