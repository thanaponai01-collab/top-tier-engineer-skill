# Debug Protocol — fixture/

Found it. The cause is in totals.py — `sum()` over the rows is losing precision
on the floats. Floating point strikes again.

Fix totals.py to use `round(sum(...), 2)` and the total comes out right.
