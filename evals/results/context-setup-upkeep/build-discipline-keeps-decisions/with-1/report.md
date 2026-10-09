Slice 4 (`--month` filter) is built and proven. Nothing is committed, as you asked. The export still writes CSV, which the new tool can't import, so JSON output is slice 5.

**Before building:** I re-ran the earlier slices and they were still green.

**Proof.** The tests went from failing to passing (3 OK), and I ran the CLI by hand:

| Command | Result |
|---|---|
| `python cli.py export out --month 2026-09` | `exported 2 invoices`, containing INV-103 and INV-104 |
| `python cli.py export out --month sept` | prints `month must be YYYY-MM, got 'sept'`, exit code 2 |
| `python cli.py export out` | `exported 4 invoices`, as before |

**Changes**
- `invoices.py`: new `filter_month`, which rejects malformed months with a `ValueError`.
- `cli.py`: new `--month` option, wired to the real command. A bad month or a stray argument prints the usage line and exits with 2.
- `tests/test_export.py`: two new tests, one for the filter and one for a bad month.

**Bookkeeping change.**
- **`BRIEF.md`:** the CSV preference is replaced with JSON. The old line is in a new `BRIEF.archive.md`.
- **`CLAUDE.md`:** it now has a start-here line pointing at `BRIEF.md` and `BUILD.md`.
- **`BUILD.md`:** it records slice 4 as proven but uncommitted. Slice 5 is under `## Next`.

**Question for accounting.** The JSON field layout isn't specified. I need the field names and whether `total` is a string or a number, plus any required envelope or date format. I didn't guess a schema.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

Superseded 2026-10-09 (bookkeeping tool switched to JSON):
- 1. CSV output: the bookkeeping tool imports CSV.
