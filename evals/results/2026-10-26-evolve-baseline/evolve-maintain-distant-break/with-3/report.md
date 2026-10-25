The dashboard now computes each order's total once. Rendering 5 orders used to compute `Order.total` 23 times; now it's 5. All CLI output is unchanged, and all 7 tests pass (4 old, 3 new). Nothing is committed.

**One difference from what you asked for:** the cache is in the dashboard, not on `Order.total`. I tried caching on `Order` first, on a scratch copy, and it broke two things:
- **Refund receipts showed the old total.** `billing/refunds.py` adds the refund line to `order.lines` directly instead of going through `add_line`, so the cache never cleared. The receipt said "New total $179.89" when it should be $89.90.
- **Restoring a backup crashed.** `ops/backup.py` saves every attribute of each order, so the cached value got saved too, and `restore` failed with `TypeError: ... unexpected keyword argument '_total'`.

A safe cache on the model would need to clear itself whenever a line is added or edited, which reaches into the refund, backup and `Line` code. That's more than this fix needed, so I kept the change in one file.

**The change** is in `reports/dashboard.py`. `render()` works out each order's total once and passes the numbers to `top_orders`, `by_customer` and `share_of_revenue`. Those functions take them as an optional `totals=` argument, so existing calls without it still work. A note at the top of the file explains why the cache lives there.

**Tests**, in the new file `tests/test_dashboard.py`:
- `test_dashboard_computes_each_order_total_once` checks that each total is computed once and the output is right. It fails on the original code, so it does test the fix.
- `test_refund_receipt_shows_new_total` and `test_backup_restore_round_trip_after_reading_total` protect against someone adding the cache to `Order` later. They pass on both the original and new code, and fail on the version cached on `Order`.

**How I checked nothing else changed:** I ran `list`, `dashboard`, `show`, `refund`, `backup`, `restore` and `list` again on copies of the project, before and after. The output was identical. `data/orders.json` in `fixture/` was never touched, and I deleted the copies. Running the tests left a `__pycache__` folder in `fixture/`.

**Left as is:** if other code ever reads `Order.total` in a loop, it will still recompute it each time. Fixing that properly means a cache on `Order` that clears itself when lines change, a bigger job I'd do separately.