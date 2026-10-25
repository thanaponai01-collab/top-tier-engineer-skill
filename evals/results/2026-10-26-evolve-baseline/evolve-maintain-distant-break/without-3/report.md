`Order.total` is now cached, so each order works out its total once and reuses it until something changes. All 9 tests pass: the 4 existing ones plus 5 new ones. I ran `list`, `dashboard`, `refund`, `list`, `backup`, `restore` and `show` on a copy of the fixture before and after the change, and the output was exactly the same both times. Nothing was committed.

**The two places a simple cache would have broken things:**
- **Refunds.** `billing/refunds.py` adds the refund line straight onto `order.lines`, skipping `add_line`. If the cache were only cleared in `add_line`, the refund receipt and the order's new status would use the old total.
- **Backup/restore.** `ops/backup.py` saves every attribute on each order. If the cache were stored on the order itself, it would end up in backup files, and `restore` would then crash when rebuilding orders from them.

**How it works now** (all in `orders/model.py`):
- The cache is kept in a separate lookup table rather than on the order, so orders have the same attributes as before and backups don't change.
- A counter goes up whenever anything that could change a total happens. That covers adding, removing or replacing lines in any way (including direct list edits like the refund's), assigning a new `lines` list, or changing a line's fields. A cached total is only reused if nothing has changed since it was computed.
- The counter is shared by all orders, so any change makes every order recompute its total once. That doesn't matter for the dashboard, which only reads totals.

The new tests in `tests/test_model.py` check that the total is computed only once, that each kind of change makes it recompute, and that no cache attribute shows up on the order.