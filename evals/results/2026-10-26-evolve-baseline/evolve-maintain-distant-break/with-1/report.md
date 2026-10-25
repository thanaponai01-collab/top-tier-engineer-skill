`Order.total` is now computed once per order and cached until the order's lines change. All 8 tests pass (4 old, 4 new), and every CLI command prints exactly what it printed before. Nothing is committed (the folder isn't a git repo anyway).

**Type of change:** an Improve: same behaviour, less work. The change is confined to `orders/model.py`. No callers, stored data or backup format changed.

**Why it was slow:** `total` re-summed every line on each access, and the dashboard reads it many times per order (to sort, to total per customer, for revenue share, and for each printed row). I found this by reading the code, not by profiling.

**Two traps a simple cache would have hit:**
- **Refunds:** `billing/refunds.py` appends to `order.lines` directly and skips `add_line`. A cache that's only cleared in `add_line` would report the wrong total after a refund and set the wrong status.
- **Backups:** `ops/backup.py` saves every attribute on the order on purpose, so new fields are never left out. A cache stored on the order (e.g. `functools.cached_property`) would land in `backup.json`, and then `restore` would crash on the extra key.

**The fix:** `order.lines` is now a small list subclass, `_Lines`, that stores the summed total and clears it on every change to the list (`append`, `pop`, `del`, `+=` and the rest). `Order` also wraps any list assigned to `lines`. So the cache never shows up in backups, and it is correct whichever code path changes the lines.

**How I checked it:**
- Before editing, I ran the tests and every command (`list`, `show`, `dashboard`, `backup`, `refund` ×2, `restore`) on a scratch copy and saved the output and resulting data. After the change, the same run matched exactly, and the backup still contains only `customer, id, lines, status`.
- New tests in `tests/test_model.py` check that:
  - 100 reads of `total` compute each line once;
  - a refund updates the total;
  - replacing or deleting lines updates it;
  - backup then restore works after `total` has been cached.
- I confirmed the new tests can fail. The original model fails the compute-once test. A `cached_property`-style cache fails the refund, reassignment and backup tests. A cache cleared only in `add_line` fails the refund test.
- `data/orders.json` is unchanged: all runs used copies.

**One limit:** the cache assumes a line's price and quantity don't change after it is created. Nothing in the code does that today, and the `_Lines` docstring says so. If something later edits `line.qty` directly, that order's total would go stale.