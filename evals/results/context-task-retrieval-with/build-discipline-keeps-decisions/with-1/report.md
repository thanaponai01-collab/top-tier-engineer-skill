I built slice 4: `--month YYYY-MM` now exports only that month's invoices. Nothing was committed. `fixture/` isn't actually a git repo, so I couldn't check the commit hashes in `BUILD.md` against any history.

**The export still writes CSV.** You said accounting's new tool takes JSON, so as things stand the file won't import. I recorded the change and made the JSON switch the next slice, but didn't build it, because I don't know what JSON layout the new tool expects (field names, and whether totals are strings like `"999.00"` or numbers). The quickest fix is a sample import file from accounting.

| Slice | Proof line | Status | What you can now do |
|---|---|---|---|
| 4 | `python cli.py export OUT --month 2026-09` → `exported 2 invoices` (INV-103, INV-104); `--month 2026-9` → exit 2, nothing written | **proven** (I ran it), uncommitted | Export a single month |

**How it's built**
- `in_month()` in `invoices.py` does the filtering.
- `cli.py` accepts `--month` and checks it before writing anything. A malformed month (`2026-9`, `2026-13`, `sept`) or a missing value prints a message and exits 2 without creating a file.
- New tests are in `tests/test_month.py`.
- Before writing any code I re-ran the earlier slices: tests passed and `cli.py export` printed `exported 4 invoices`.

**Proof** (the new tests failed first, with `exported 4 invoices`, because the flag was being ignored; they pass now):
```
Ran 4 tests ... OK
$ python cli.py export /tmp/sep.csv --month 2026-09
exported 2 invoices to .../sep.csv          exit 0
id,date,customer,total
INV-103,2026-09-02,Ardent Ltd,999.00
INV-104,2026-09-19,Corvo GmbH,3100.00
$ python cli.py export /tmp/bad.csv --month 2026-9
--month must be YYYY-MM, got '2026-9'       exit 2   (no file written)
$ python cli.py export /tmp/all.csv
exported 4 invoices                         exit 0
```

**Changed on review:** the missing-value test originally wrote to `out.csv` in the working directory. When it failed before the fix it left a stray file there, so I deleted the file and moved the test into a temp directory.

**Where things were recorded**
- **JSON switch:** written into `BRIEF.md` as Preferences 1, replacing the CSV line, which moved to the new `BRIEF.archive.md`.
- **Slice 4 and the next step:** `BUILD.md` has slice 4 marked proven and uncommitted, and `## Next` is now slice 5 (JSON output), with its proof line and the open question about the JSON layout.
- **Start-here block:** added to `CLAUDE.md`, linking `BRIEF.md` and `BUILD.md`.
- **Deferred:** nothing.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

Lines replaced in `BRIEF.md`, newest first.

## 2026-10-13 — Preferences 1, replaced by JSON output
1. CSV output: the bookkeeping tool imports CSV.
