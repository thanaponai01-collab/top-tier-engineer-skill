Slice 4 is built and proven. `python cli.py export OUT --month YYYY-MM` now exports only that month's invoices. I haven't committed anything, and BUILD.md marks the slice as uncommitted.

| Slice | Proof | Status |
|---|---|---|
| 4: month filter | `--month 2026-09` printed `exported 2 invoices` and wrote only INV-103 and INV-104 | proven |
| 4: bad month | `--month 2026-13` printed `month must be YYYY-MM, got '2026-13'`, exited 2 and wrote no file | proven |

- **Tests:** `python -m unittest discover tests` passes with 5 tests. That includes the four new ones, which failed before the change. I also re-ran the earlier slice first, and it was still green.
- **Where it landed:** the `invoices_for_month` function is in `invoices.py`, and `cli.py` calls it.
- **Unchanged behavior:** `export OUT` with no `--month` still exports all 4 invoices.

**The JSON switch is not built.** The brief lists CSV only as a tradeable preference, so moving to JSON is allowed, but I don't know the shape the new tool expects. I've queued it in BUILD.md as slice 5. I need three things from accounting:
- the field names;
- whether `total` is a string like `"1250.00"` or a number;
- whether the file is a bare array or wrapped in an object.

The month filter doesn't depend on the output format, so none of this work needs redoing. BRIEF.md still says CSV. I've put updating it on the Deferred list until the format is confirmed.