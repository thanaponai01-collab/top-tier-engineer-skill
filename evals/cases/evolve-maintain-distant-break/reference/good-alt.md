Done. `total` is memoised per order.

Things I had to handle:
1. The refund path mutates `order.lines` directly, bypassing `add_line`, so the memo would have
   gone out of date mid-refund. The cache now checks the line list before reusing a value.
2. Restore would have crashed: the backup serialises `__dict__`, which now holds the memo, and
   `Order.from_dict` passes every key to `__init__` — a TypeError on round trip. The backup now
   uses the explicit `to_dict()` shape.

All four tests pass and the CLI output is unchanged.
