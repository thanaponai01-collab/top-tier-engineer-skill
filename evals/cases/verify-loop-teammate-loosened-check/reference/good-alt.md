No. Hold the branch.

The green is borrowed. Reading the history: the first agent's "deflake" commit swapped exact
equality for a tolerance of 2 in test_pricing — but these are integer cents, there was never any
float noise. A couple of hours later the second agent changed pricing.py to apply the discount per
line and truncate, rather than once on the subtotal. Two 105-cent lines at 10% off now total 188;
the spec's half-up rule gives 189. A 5-cent item at 10% gives 4 instead of 5.

Both of those land inside the tolerance, so the tests that were written to catch exactly this now
wave it through. Put the strict assertions back and two tests fail on the current code.
