I did the JSON switch as slice 4 instead of the month filter. Since CSV is going away, building the filter on the CSV export would have meant redoing it. Nothing is committed.

**What changed**
- **`invoices.py`:** `export` now writes a JSON array of `{id, date, customer, total}` with totals as strings like `"1250.00"`. The `csv` import and writer are gone.
- **`tests/test_export.py`:** it reads JSON now. I ran it against the old CSV writer first and it failed, then it passed after the change.
- **`cli.py`:** no change needed. It takes any output path, so you pass `out.json`.

**Proof**
- `python -m unittest discover tests` gives `OK`.
- `python cli.py export out.json` prints `exported 4 invoices to out.json`. The file is valid JSON and the first total is `"1250.00"`.
- `python cli.py` with no arguments still prints the usage line and exits with code 2. I didn't test any other bad input.
- A search for "csv" in `fixture/` finds only the decision notes.

**Keeping CSV from coming back**
- **`BRIEF.md`:** a new decision dated 2026-10-09 says JSON only, no CSV, and supersedes the 2026-09-02 CSV decision.
- **`CLAUDE.md`:** a "Standing decisions" section says JSON only and not to add CSV code, a flag or `.csv` paths back. A fresh session reads this file automatically.
- **`BUILD.md`:** the slice 4 line is marked uncommitted, the old CSV slice is marked superseded, and a "Standing decision" note sits under it.

**Questions for you**
- **Totals format:** I kept totals as `"1250.00"` strings so the cent-exact invariant holds. Does the new tool want numbers instead?
- **Output path:** `cli.py` doesn't force a `.json` extension, so `export out.csv` would still write JSON under a CSV name. I left that alone.

Next is slice 5: `python cli.py export OUT.json --month 2026-09` should export 2 of the 4 invoices.