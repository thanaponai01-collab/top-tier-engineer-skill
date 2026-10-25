`Order.total` is now computed once per order and cached. I rendered the dashboard twice on the real data and `subtotal()` ran 10 times, once per line. Before, it ran on every read of `total`. Nothing is committed.

**What changed**
- **`orders/model.py`:** `total` saves its result after the first calculation. Calling `add_line()` or assigning a new `lines` list clears it, so the next read recalculates.
- **Kept out of backups:** backups save every attribute an order object has. If the cached total were a normal attribute, it would end up in the backup file, and `restore` would then fail on the unknown field. So the cache is stored separately from the order's normal attributes, and an order still exposes only `id`, `customer`, `status` and `lines`.
- **`billing/refunds.py`:** the refund added its credit line straight onto `order.lines`, which skips the cache reset. Without a fix, the refund's status and "New total" would have used the old, pre-refund total. It now goes through `order.add_line(credit)`. That was the only place in the repo that changed an order's lines directly.

**How it was checked**
I followed `evolve-maintain`. I recorded eight commands on the original code: `list`, `show`, `dashboard`, `refund`, `backup`, the unit tests, a backup→restore→list round trip, and two refunds followed by dashboard, backup, restore and `show`. Each one prints the same output and writes the same files after the change. All 15 places that read `total`, `lines` or the refund were run by at least one of those commands, and the gate reported done. The unit tests pass (4/4).

**Not covered**
- **Editing lines directly goes stale:** any code that changes `order.lines` itself, or edits a line's price or quantity, will see an out-of-date total. There is none in this repo, and there's a comment at `total` saying to use `add_line`, but code outside the repo could do it.
- **Old data:** existing `data/orders.json` files and old backups still load, because what gets saved hasn't changed.

The README doesn't need updating. I deleted `.evolve/` afterwards.