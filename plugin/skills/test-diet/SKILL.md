---
name: test-diet
description: >-
  Make tests shorter to read and faster to run without losing a single bug they catch: every test checked, tests that catch nothing the others miss, dead tests for code no longer used or that never run, setup copied across tests, slow tests and why, tests that only check mocks; slimmed, with numbers before and after and planted bugs showing nothing was lost, plus a quick command to run while working. Use for "my tests are too long", "tests are slow", "too many tests", "old tests", "clean up the tests", "too much setup in tests".
disable-model-invocation: true
metadata:
  stage: review
  card: "shorter, faster tests that still catch every bug"
---

# Test diet

Make the tests shorter to read and faster to run, and lose nothing they catch. Suites grow because
each change adds its own tests and nobody removes any: a new test repeats a check an older one
already makes, tests stay for code that was removed or is no longer called, skipped tests are never
looked at again, and many tests walk the same path through the app (make a user, verify, add to the
cart, pay) just to reach the state one of them checks. Some are slow because of a sleep, the
network, a started process or setup rebuilt each time; some only check what a mock was told.
Shortening is easy. Doing it without losing a bug the old tests would have caught is the hard part,
and a reader cannot see that loss, so it is measured. Deleting, merging and parametrizing tests is
allowed; fewer tests is fine, fewer bugs caught is not. How you find and slim is up to you.

**What done looks like**

- Before any change, the old suite was run and recorded: tests, test lines, total time and each
  test's time, and which small bugs planted in the app code the tests import (a flipped comparison,
  `and` for `or`, `+` for `-`, an off-by-one) each test catches. Planted bugs are undone afterwards.
- Every test was looked at, not only the obvious leads. A test that catches no planted bug the
  others miss is merged or deleted, unless it checks something planted bugs cannot show (an error
  message, a file written, a slow path); then it is kept with that reason.
- Dead tests are gone: tests for code that no longer exists or nothing calls, tests skipped or
  marked expected-to-fail with no live reason, tests the runner never collects, commented-out tests.
- Every repeated setup, slow test and mock-only test is slimmed or kept with a reason. A repeat
  becomes a fixture, a builder or a helper that starts in the needed state; a slow test is at least
  twice as fast; a mock-only test checks a real result, or is deleted when another test holds it.
- A quick command runs in a few seconds and catches most planted bugs, for use while working; the
  full suite is for before a commit. Its share of planted bugs caught is stated.
- The new suite passes, has no more test lines and is not slower, and catches every planted bug the
  old one caught. A planted bug now missed means a removed check was the only one holding that
  code: put it back.

**Avoid**

- Changing app code. Only test files and test-runner config change. Files git ignores, such as
  caches the test run writes, are not app code. A test slow because of the app (a retry sleep) is
  kept, with that reason. App code that only the tests still call is reported, not removed.
- Counting a test as faster or a bug as caught without running it after the last change.
- Claiming order dependence or flakiness was checked when it was not.

**The answer**

```
Before -> after: <n> tests, <n> lines, <s> s  ->  <n> tests, <n> lines, <s> s
Planted bugs caught: <n> of <n> before, <n> of <n> after (none lost)
Quick check: `<command>`: <s> s, catches <n> of <n>
Removed: <test> (<file:line>): <dead, or which tests already catch its bugs>   (one line each)
Changed: <what, in plain words> (<file:line>)                                    (one line each)
Kept: <test or setup> (<file:line>): <why>                                        (or: none)
App code only tests use: <name> (<file:line>)                                     (or: none)
Not checked: <run order, flakiness, languages with no planted bugs>
Tests: `<command>`: passed before and after
```
