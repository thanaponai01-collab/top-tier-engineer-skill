Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only September's two invoices. Nothing is committed, as you asked, and the folder has no git repo anyway.

**Proof**
- The previous slice's test was green before I started.
- I added two tests that failed first. One checks that `--month 2026-09` exports INV-103 and INV-104. The other checks that `--month 2026-13` returns 2 and writes no file.
- `python -m unittest discover tests` now passes with 3 tests.
- Running the real command with `--month 2026-09` printed `exported 2 invoices to o.csv`, and the file holds exactly INV-103 and INV-104. Running without `--month` still exports all 4. A bad month prints the usage line and exits 2.

**Changes**
- `invoices.py`: `load_invoices(month=None)` filters by the date prefix.
- `cli.py`: parses and validates `--month YYYY-MM`.
- `tests/test_export.py`: the two new tests.

**JSON decision**
- I recorded it in `BRIEF.md`: preference 1 now reads "JSON output", and a `## Decisions` entry dated 2026-10-09 notes it. The old CSV line moved to `BRIEF.archive.md`.
- The export still writes CSV. I kept this slice to the month filter and queued the JSON change as slice 5 under `## Next` in `BUILD.md`.
- Until slice 5 is done, accounting's new tool can't import the file.
- Before slice 5, I need the exact JSON shape the new tool expects. Specifically, should totals be a string like `"1250.00"` or an integer in cents? I haven't guessed.

`BUILD.md` also lists slice 4 as proven but uncommitted.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

- (replaced 2026-10-09) Preference 1. CSV output: the bookkeeping tool imports CSV.
