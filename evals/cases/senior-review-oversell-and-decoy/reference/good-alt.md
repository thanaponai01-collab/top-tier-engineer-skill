What I opened: all four files in `fixture/` — `inventory.py`, `cli.py`, `test_inventory.py`,
`README.md`. Nothing skipped; there isn't much here. Verdict: not safe yet, and the fix is small.

The tool's one job (README.md): reserve warehouse stock for an order, one at a time, never letting a
reservation exceed what's actually on the shelf.

I tried to break it rather than guess. Cheapest first:

1. No args — `python cli.py widget` throws `IndexError`. Fine, that's just a missing CLI argument.
2. A qty bigger than what's in stock — `python cli.py widget 999` — this is the one that matters,
   and I ran it: it printed `-989`. `reserve_stock` subtracts qty from `_STOCK[item]` and returns the
   result with no check that qty is positive or that it fits what's available. That's an oversell:
   the tool just told a warehouse worker they reserved 999 widgets they don't have, silently.
3. Concurrent callers — I did not attempt this one. Per README.md the tool is single process with
   no concurrent access: each run is its own `python` invocation reserving one order and exiting.
   There's nothing here that lets two callers run at once, so I'm marking this traced, not proven,
   and not claiming a race condition I can't produce.

Failure mode: none. No exception is raised and nothing is logged — the caller just gets `-989`
printed and the corrupted stock count is already saved in `_STOCK`.

Where the next change lands: `inventory.py` is one small file and `reserve_stock` is the only entry
point, so the fix is localized.

Biggest gap, and the one finding here: `reserve_stock` (inventory.py:5) needs to validate qty
before mutating stock — reject anything outside `0 < qty <= get_stock(item)` — proven by the -989
output above, not by reading the code and guessing. `git log -S reserve_stock` shows this was never
attempted and dropped; it was simply never written.

One thing I'm deliberately not flagging: the bare module-level `_STOCK` dict, with no lock, looks
like a red flag on its own, but this is a single-process tool per the README — there's no concurrent
access to run and no way to prove a race here, so calling it a bug would be a guess dressed up as a
finding.
