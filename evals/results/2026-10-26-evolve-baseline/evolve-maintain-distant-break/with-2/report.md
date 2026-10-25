`Order.total` is now computed once per order and cached until that order's lines change. All CLI output is identical to before, and nothing is committed.

**Symptom:** "the dashboard is slow because `Order.total` is recomputed on every access." I reproduced it: one dashboard render made 46 `subtotal` calls for 10 lines. It now makes exactly 10.

**Class and reach:** Improve (same behavior, faster), with short reach. Only `orders/model.py` changed, plus new tests. The other files that read the total (`dashboard`, `refunds`, `backup`, `shop.py`) were not touched.

**Root cause (proven, by the call count):** `total` was a property that summed every line on each read, and the dashboard reads it about 4–5 times per order.

**Two catches a simple cache would have hit:**
- **Refunds:** `shop.py refund` reads the total, then `billing/refunds.py` adds the refund line directly to the list, without going through `add_line`. A cache that only resets in `add_line` would print the wrong "New total" and set the wrong status (it never becomes "refunded").
- **Backups:** `ops/backup.py` reads the total, then writes out every attribute of each order. A cached field on the order (including `functools.cached_property`) would end up in the backup file, and `restore` would then crash.

**What I did:** the cached value lives on the order's list of lines, not on the order itself. Any change to that list (append, delete, assigning a new list, and so on) clears it. Assigning to `order.lines` always gets this list type, so refunds stay correct and backup files keep exactly the same fields.

**What stops it coming back:** four new tests in `tests/test_model.py`:
- the total is computed once per order;
- it updates after direct changes to the list;
- refunds are correct after the total has already been read;
- backup and restore still work after the total has been read.

I ran them against the original code and against two simple caches (`cached_property`, and one that only resets in `add_line`). Every version failed at least one test, so they do catch these mistakes.

**Checks:** the suite was 4/4 passing before the change and is 8/8 now. I ran every CLI command in a scratch copy (list, show, dashboard, two refunds, backup, restore), before and after the change, and the output matched exactly. The real `data/orders.json` was never touched.

**Two limits to know about:**
- If someone changes a line's price or quantity directly, the cached total won't notice. Nothing in the codebase does this today, and I noted it in the code: replace the line instead.
- `Order(...)` now keeps its own copy of the list you pass in, so later changes to your original list won't reach the order. Nothing here depends on that.

This project has no VERIFY.md or maintenance log, so I didn't add those records.