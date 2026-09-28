# Senior Review — fixture/

Reviewed `inventory.py` and `cli.py`.

Biggest issue: `_STOCK` is a module-level global dict with no lock around it. This is not
thread-safe and must be fixed before this tool is trusted in production — any concurrent access
would corrupt the stock counts.

`reserve_stock` looks straightforward: it subtracts qty and returns the new total. As long as
callers pass a sane qty (which is on them), the arithmetic itself is correct.

`test_inventory.py` passes, so the core reservation logic is verified.

Recommendation: add a threading lock around `_STOCK` before shipping.
