`Order.total` is now worked out once per order and reused. I ran all eight recorded commands again after the change, and every one printed and wrote the same thing as before. Nothing is committed.

**What changed**
- **`orders/model.py`:** the first read of `total` adds up the lines and saves the result; later reads return the saved value. `add_line()` clears the saved value so the next read recomputes it. In a quick check, 100 reads of `total` on a two-line order added up the lines only once.
- **`billing/refunds.py`:** refunds used to add the credit line straight onto `order.lines`, so the saved total would have been out of date. They now go through `order.add_line(credit)`, so the receipt's "New total" and the refunded status stay correct.

**A trap I avoided:** backups (`ops/backup.py`) write out every field of each order. If the saved total were stored as an ordinary field, it would appear in backup files, and `restore` would then crash on that unexpected field. So I stored it in a slot (`__slots__ = ("__dict__", "_total")`), which keeps it out of the dumped fields. Backup files come out exactly as before, and the order still has only `id`, `customer`, `lines` and `status`.

**How I checked it**
- Before editing, I recorded these commands on the original code: `list`, `show`, `dashboard`, `refund`, `backup`, backup then restore then list, refund then list then dashboard, and the test suite.
- After the change, the skill's check confirmed:
  - all eight still print and write the same output;
  - each of the 7 places that use `total` or the refund code was actually run by at least one command;
  - the 4 unit tests pass.
- I deleted the `.evolve/` folder afterwards, as the skill asks.

**Not covered**
- Any code that changes `order.lines` directly, or edits a line's price or quantity after `total` has been read, will now get an old total. Nothing in this repo does that, and there's a comment on `total` saying to use `add_line()`. Callers outside this repo aren't covered.
- Saved data (`data/orders.json` and existing backups) never contained the total, so it isn't affected.