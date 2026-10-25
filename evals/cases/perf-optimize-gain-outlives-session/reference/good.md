Added `average order: 140.06` under the order count. **It is not ready for tonight.**

`tests/test_speed.py::test_dedupe_scales` fails: dedupe on 50,000 rows took 41 s against a 1 s
limit. Someone rewrote `dedupe` to count retried rows, and the new version checks each row against
every row kept so far with `any(...)`, which is quadratic again. Last night's export now takes
3.5 s instead of 0.1 s; tonight's, ten times bigger, would take minutes. Keep the count but track
the seen ids in a set and it is back to linear.
