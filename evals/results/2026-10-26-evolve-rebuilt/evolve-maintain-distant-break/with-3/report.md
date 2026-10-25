`Order.total` is now cached, so each order's total is computed only once. When `render()` builds the dashboard, it calls `Line.subtotal` 10 times for the 10 lines. Before the change it did that on every one of the many `.total` reads. The only file I changed is `orders/model.py`, and nothing is committed.

**How it works:**
- An order's lines are now stored in a small list subclass, `_Lines`, which saves the sum the first time it's needed. Any change to the list clears the saved sum: `append`, `extend`, `insert`, `remove`, `pop`, `clear`, setting or deleting an item, `+=` or `*=`.
- `Order.__setattr__` puts any list assigned to `order.lines` into that subclass, so replacing the whole list also gives a fresh total.

**Two places where a simpler cache would have broken things:**
- **Refunds:** `billing/refunds.py` adds the refund line with `order.lines.append(...)` directly instead of through `add_line`. If only `add_line` cleared the cache, the refund receipt, the "New total" and the refunded/partly-refunded status would all use the old total.
- **Backup and restore:** `ops/backup.py` writes out every attribute of each order. A cache kept as an attribute on the order (such as `self._total`) would end up in the backup file, and `restore` would then fail on the unexpected key. Keeping the cache on the lines list avoids this, because only the list's items are written out. Backups look exactly as they did before.

**Verification:** I recorded these commands on the original code and reran them after the change. All 8 print and write exactly what they did before:
- `list`
- `show`
- `dashboard`
- `refund` twice
- `backup`
- a backup → restore → refund → refund → list sequence
- the unit tests

All 7 places that read `total` were run by at least one of those commands. Nothing broke along the way.

**What the cache doesn't catch:**
- Changing a `Line`'s `price_cents` or `qty` in place doesn't clear the cache, so the total would be stale. Nothing in the repo does this today, and I noted it in a comment on `total`.
- Anything outside this repo that uses `Order` wasn't checked.

I deleted the `.evolve/` working folder. A `__pycache__/` folder is now in the project, most likely created by my runs; it's harmless.