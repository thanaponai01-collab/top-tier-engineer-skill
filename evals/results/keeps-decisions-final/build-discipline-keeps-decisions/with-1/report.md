Slice 4 is done and proven: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. I didn't commit, and `BUILD.md` records it as uncommitted.

I re-ran the last proven slice first, and the tests passed. I wrote the two new tests before the code, and both failed. Afterwards `python -m unittest discover tests` printed `OK`.

| Slice | Proof | Status |
|---|---|---|
| 4: `--month` | `export o.csv --month 2026-09` gave `exported 2 invoices to o.csv`, with INV-103 and INV-104 in the file. Without `--month` it still gave 4. | proven |
| 4: bad month | `--month Sept` printed `bad --month 'Sept', expected YYYY-MM`, exited 2 and wrote no file. | proven |

**JSON change:** accounting's new tool takes JSON, but the export still writes CSV. The `--month` filter doesn't depend on the format, so I finished slice 4 as asked and didn't change the format.
- **`BRIEF.md`:** Preference 1 now says JSON output. The old CSV line is in `BRIEF.archive.md`.
- **`CLAUDE.md`:** I added a start-here block that links `BRIEF.md` and `BUILD.md`.
- **`BUILD.md`:** slice 5 is next: write JSON instead of CSV. I haven't decided whether `total` is a string like `"1250.00"` or a number, and that choice needs to keep totals exact to the cent.

Nothing is deferred.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

Superseded lines, moved verbatim from BRIEF.md.

- 2026-10-09 Preferences 1: CSV output: the bookkeeping tool imports CSV.
  (Replaced: accounting switched bookkeeping tools; the new one takes JSON, not CSV.)
