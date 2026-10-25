`Order.total` is now computed once per order and reused, so the dashboard no longer re-adds the lines on every read. The only file I changed is `fixture/orders/model.py`, and nothing is committed.

**How it works:** the total is cached on the order's list of lines, and any change to that list clears the cache. I did it this way because of two parts of the code:
- **Refunds** (`billing/refunds.py`) add a line with `order.lines.append(...)` directly, not through `add_line`. A cache that only reset in `add_line` would show the old total right after a refund.
- **Backups** (`ops/backup.py`) save every attribute on the order and rebuild it with `Order(**d)`. A cache stored as an extra field on the order would get saved into backup files and then break restore. Keeping it on the list avoids that, and the list is still written to JSON as a plain list.

If code replaces the whole list (`order.lines = [...]`), the order switches it to the caching list automatically.

**Checks I ran:**
- The 4 existing tests pass, and `shop.py dashboard` produces its usual report.
- Five reads of `total` add up the lines once.
- A refund updates the total and the order status correctly.
- Replacing the list and using `+=` both give the right totals.
- A backup contains no cache field and restores with the right total.

**One limit:** changing a field on a line that is already in an order (e.g. `line.qty = 5`) won't clear the cache, because a line doesn't know which order it belongs to. Nothing in the code does that today, but if something starts to, it should replace the line in the list or go through the order instead.