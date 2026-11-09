---
name: test-diet
description: >-
  Make tests shorter to read and faster to run without losing a single bug they catch: setup copied across tests, slow tests and why, tests that only check mocks; slimmed, with numbers before and after and planted bugs showing nothing was lost. Use for "my tests are too long", "tests are slow", "clean up the tests", "too much setup in tests".
disable-model-invocation: true
metadata:
  stage: review
  card: "shorter, faster tests that still catch every bug"
---

# Test diet

Make the tests shorter to read and faster to run, and lose nothing they catch. Long tests hide
structure nobody declared: many tests walk the same path through the app (make a user, verify, add
to the cart, pay) just to reach the state one of them checks; the same setup block is copied by
hand; tests are slow because of a sleep, the network, a started process or setup rebuilt each time;
some tests only check what a mock was told. Shortening is easy. Doing it without losing a bug the
old tests would have caught is the hard part, and a reader cannot see that loss, so it is measured.
Deleting, merging and parametrizing tests is allowed; fewer tests is fine, fewer bugs caught is not.
How you find and slim is up to you.

**What done looks like**

- Before any change, the old suite was run and recorded: tests, test lines, total time and each
  test's time, and which small bugs planted in the app code the tests import (a flipped comparison,
  `and` for `or`, `+` for `-`, an off-by-one) it catches. Planted bugs are undone afterwards.
- Every repeated setup, slow test and mock-only test found is slimmed or kept with a reason. A
  repeat becomes a fixture, a builder or a helper that starts in the needed state; a slow test is
  at least twice as fast; a mock-only test checks a real result, or is deleted when another test
  already holds that behavior.
- The new suite passes, has no more test lines and is not slower, and catches every planted bug the
  old one caught. A planted bug now missed means a removed check was the only one holding that
  code: put it back.

**Avoid**

- Changing app code. Only test files change (tests folders, `test_*` files, `conftest.py`). Files
  git ignores, such as caches the test run writes, are not app code. A test slow because of the app
  (a retry sleep) is kept, with that reason.
- Counting a test as faster or a bug as caught without running it after the last change.
- Claiming order dependence or flakiness was checked when it was not.

**The answer**

```
Before -> after: <n> tests, <n> lines, <s> s  ->  <n> tests, <n> lines, <s> s
Planted bugs caught: <n> of <n> before, <n> of <n> after (none lost)
Changed: <what, in plain words> (<file:line>)              (one line each)
Kept: <test or setup> (<file:line>): <why>                  (or: none)
Not checked: <run order, flakiness, languages with no planted bugs>
Tests: `<command>`: passed before and after
```
