`Order.total` is now computed once per order and reused until the order's lines change. A test showed 100 reads of `total` running the line sum once. The only file changed is `fixture/orders/model.py`, and nothing is committed.

**How it works:** `Order.lines` is now a small `list` subclass (`_Lines`) that holds the cached total. Every method that changes the list (`append`, `extend`, `pop`, `__setitem__`, `__delitem__`, `+=` and the rest) clears the cache.

**Why the cache isn't on the order itself:** the obvious fixes (`functools.cached_property` or `self._total`) would have broken two things:
- **Refunds:** `billing/refunds.py` adds the refund line with `order.lines.append(...)` directly, not through `add_line`. A cache that only `add_line` clears would print the old total on the receipt and set the wrong status.
- **Backup and restore:** `ops/backup.py` writes every attribute of each order to the file. A cached total stored on the order would end up in the backup, and `restore` would then fail because `Order` doesn't accept a `_total` argument. The cache lives on the list, and JSON saves only the list's items, so backups are unchanged. I checked that the backup file has no `total` key.

**Checks I ran:**
- All 4 existing tests pass.
- I ran `dashboard`, `backup`, `restore`, `list`, `refund A-1001 L2` and `show`. The refund printed the correct new total ($89.90) and set the status to "partly refunded". I restored `data/orders.json` afterwards.
- A quick check confirmed the total updates after an append, an item replacement and a delete.

**Limitations:**
- If code replaces `order.lines` with a new plain list, `total` stays correct but isn't cached for that order. Nothing in the code does this today.
- Changing a line's `price_cents` or `qty` directly isn't detected, so the total would be stale. Nothing in the codebase does this either; lines are only added. If that might happen later, the lines themselves would need to be made read-only or made to clear the cache.