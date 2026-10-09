I switched the export to JSON, removed CSV, and added the `--month` filter. Nothing is committed. `fixture/` isn't a git repo, and you said not to commit. The 4 tests pass, and I ran the CLI by hand.

| Slice | Proof | Status |
|---|---|---|
| 4 (new): JSON replaces CSV | A test reads the JSON back and checks `"1250.00"` and `"480.50"`. `python cli.py export out.json` printed `exported 4 invoices`. | proven |
| 5: `--month YYYY-MM` | `export x --month 2026-09` printed `exported 2 invoices` (INV-103 and INV-104). `--month sept` printed the usage text and exited with code 2. | proven |

- **Code:** `invoices.py` now writes a JSON array with `id`, `date`, `customer` and `total`, and the `csv` import is gone. Totals use integer division, so they stay exact to the cent and don't pick up float error. `filter_month` is new in `invoices.py`, and `cli.py` takes the `--month` flag.
- **Tests:** I rewrote the existing test to read JSON and added three: the month filter, the CLI month export, and a bad month.
- **Keeping CSV from coming back:**
  - `BRIEF.md` Decisions now has a 2026-10-09 entry saying JSON is the format, CSV is removed, and CSV must not be reintroduced. It replaces the old 2026-09-02 CSV entry.
  - `CLAUDE.md` carries the same rule, so a new session sees it before it reads anything else.
  - `BUILD.md` records it too.
- **Remaining "csv" mentions:** the only ones left are those notes and the old slice 2 line in `BUILD.md`. That line is marked as superseded.
- **Deferred:** a test that ids are unique across an export. It is due when a second data source is added.

Nothing is queued after this. I didn't invent a slice 6, so pick the next one from `BRIEF.md`.