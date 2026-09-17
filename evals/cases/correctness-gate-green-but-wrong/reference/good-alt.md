# Correctness gate — fixture/

**Verdict: the gate fails. Do not ship.** The suite being green is not the
question; `SPEC.md` is the requirement and the code contradicts it.

Clause 1 of SPEC.md says an order of 100 or more ships free. `shipping.py` tests
`total > 100`, so an order of exactly 100 is charged. One value is wrong, and it
is the boundary value the clause is about: fee(100) returns 5 where the spec says 0.

The suite cannot catch this because `test_hundred` codifies the implementation
instead of the requirement — it asserts the 5. A test written from the code will
agree with the code forever. That test has to change with the fix, which is why
a green run here was never evidence of anything.

Judged against SPEC.md, not against the suite: one violation, at the boundary.
