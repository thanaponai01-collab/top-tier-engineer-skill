# Correctness Gate — fixture/

**FAIL.** The suite is green and the code contradicts the spec at the boundary.

Oracle: `SPEC.md` clause 1 is an acceptance criterion written to be provable
either way — an order of 100 or more ships free. That is the oracle, not the
existing suite.

`shipping.py:4` reads `if total > 100`. At exactly 100 the spec says 0 and the
code returns 5. Proven: `python -c "from shipping import fee; print(fee(100))"`
prints `5`.

`test_shipping.py:test_hundred` asserts `fee(100) == 5`. That test asserts what
the code does, not what the spec says, so it locks the defect in. It must change
to expect 0 before the fix, and then it is the regression test.

| behavior | oracle | result | evidence |
|---|---|---|---|
| free shipping at 100+ | spec clause 1 | FAIL | proven, fee(100) == 5 |
| flat fee below 100 | spec clause 2 | pass | proven |
| negative rejected | spec clause 3 | pass | proven |

Mutation spot-check: flipping `> 100` to `>= 100` leaves the suite green, which
is the blind spot in one line.

Fix: `if total >= 100`, and correct `test_hundred`.
