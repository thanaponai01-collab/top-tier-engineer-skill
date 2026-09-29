## What to hand to whom

Short version: give the CSV export to a second agent right away; keep the discount and the tax
exemption with a single owner, one after the other.

Why. `invoice.py` holds `total()`, and both features rewrite it. If two agents each edit it, one of
two things happens: a merge conflict, or worse, a clean merge where the order the two rules are
applied in quietly changes the amount for every discounted, exempt customer. They collide, so I
would not run them in parallel. Decide the order first (discount off the subtotal, then tax, then
the exemption zeroes the tax) and let one agent build both.

The export does not share that risk. It is a new `export.py` that reads amounts by calling
`total()`; it edits no file the other two edit. It can go alongside them.

Each piece, and when it is done:

1. Discount: done when a new test with a 10000-cent invoice and 10% off returns 9630 for a Thai
   customer, and `python -m unittest` still passes.
2. Exemption: done when an exempt customer's 10000-cent invoice must equal 10000, and the four
   existing tax tests still pass.
3. Export: done when running it over the sample invoices prints a header and three rows, each amount
   equal to `total()`; that is the expected output.

When they come back: merge one at a time and rerun the full suite after every merge.

I have not run anything. This is a plan.
