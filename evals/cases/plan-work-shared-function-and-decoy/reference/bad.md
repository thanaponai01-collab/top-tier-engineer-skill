# Plan

All three changes are independent and can be given to three agents at once:

1. Discount: add a `discount_pct` field to the customer and apply it to the invoice.
2. Tax-exempt: add a `tax_exempt` flag to the customer and skip the tax when it is set.
3. CSV export: write a new file that dumps every invoice with its amount.

Each agent should add tests for their piece. Once all three are done, merge them and run the tests.
This is straightforward and the pieces do not interact, so all three can run in parallel.
