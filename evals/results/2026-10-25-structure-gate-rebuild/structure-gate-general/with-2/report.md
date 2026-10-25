**Is it spaghetti? In places.** Almost all the tangle is in one function, `compute_price`, and that's the function your new discount type has to go into. The rest is small and mostly fine, apart from two issues listed below.

**How much was measured:** 201 lines of code. A parser analysed 187 of them (93%). The other 14 lines are `fixture/static/app.js`, which the tool has no JavaScript parser for, so I read it myself. That's a reading, not a measurement. The gate passed: 3 findings, 1 unparsed file (read), verdict "in places". 12 of the 13 functions are under every threshold.

| Problem | Where | Measured | What it costs you |
|---|---|---|---|
| Tangled function | `fixture/invoicing/pricing.py:4` `compute_price` | 64 lines, complexity 32, nesting 6 | All the discount logic is inline here, mixed in with shipping and tax: 3 line kinds with 7 discount branches, 3 coupon codes and a December VIP rule. A new discount type means one more branch in this function. The order things apply in is implicit: line discounts, then coupon, then shipping, then tax. So you'd also have to decide whether the new discount counts before or after the `total > 50` check on `SAVE` coupons, and before the US free-shipping limit (under $35 pays shipping). **Only one test exists** (`tests/test_pricing.py`), and it exercises one path out of about 32. If your change breaks any other branch, the tests won't catch it. |
| Import cycle | `models.py` ↔ `store.py` | 2 modules | `store.get` uses `models.blank_order()` as the fallback for every table. So a customer ID that doesn't exist comes back as an order-shaped dict, and it gets priced anyway with no error: no country means it's charged foreign shipping (25.0) and 20% tax. On top of that, `cli.py:22` reaches the private `store._read()` through `models.store`. Moving or renaming either module breaks the other module and the CLI. |
| Copied block | `export_csv.py:6-12`, `export_json.py:6-12` | 2 copies, 7 lines each | The invoice formatting (number padding, name casing, rounding, default currency, paid/open status) is written out twice. If you want to show the discount on exported invoices, you have to make that change in both files, or the CSV and JSON exports will disagree. |
| Not parsed (read by hand) | `static/app.js` | 14 lines | It has 2 functions and 1 form-submit handler. It calls `/price` and displays `body.total`. It contains no pricing logic, so a new discount type won't touch it. However, nothing in this code serves `/price` (the CLI just prints a number), so whatever backs that page lives somewhere else. |

**Not covered:** whatever serves `/price`, which isn't in `fixture/`. Also, the analysis looked at shape, not behaviour. I didn't run the pricing rules to check they're correct.

**Before adding the discount, I'd recommend:**
1. Add a few tests that pin down how `compute_price` behaves today: service/contract, bulk tiers, clearance, each coupon, and the December VIP rule.
2. Pull the line discounts and coupons out into small separate functions, so the new type becomes its own function rather than a seventh level of nesting.
3. If invoices will show the discount, merge the two export formatters into one first.

The import-cycle fallback is a separate bug worth a ticket, but it doesn't block the discount work.

I deleted the `.structure/` notes folder afterwards. To stop this from getting worse in CI, run `scripts/structure-report.py --write-baseline FILE fixture` to save today's findings. After that, `--baseline FILE` fails only on a new or worse finding.