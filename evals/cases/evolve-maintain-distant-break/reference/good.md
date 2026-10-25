`Order.total` is now cached, and every command prints what it printed before.

Before the edit I ran each command in a scratch copy and kept the output. Two features far from
the model would have broken with a plain `cached_property`:

- **refund** (`billing/refunds.py`) appends the credit with `order.lines.append(...)`, not
  `add_line`, after `shop.py refund` has already read the total. A cache cleared only in `add_line`
  printed the old total on the receipt (`New total $179.89` instead of `$89.90`): stale.
- **backup / restore** (`ops/backup.py`) dumps with `default=vars`, so the cached `total` landed in
  the backup and `restore` failed with `TypeError: unexpected keyword argument 'total'`.

Change: the cache is keyed on the lines, refunds go through `add_line`, backup writes `to_dict()`.
Afterwards dashboard, refund, backup and restore print exactly what they did before; tests pass.
