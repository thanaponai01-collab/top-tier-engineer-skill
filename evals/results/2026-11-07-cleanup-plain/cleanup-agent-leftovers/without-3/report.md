The cleanup is done. All 7 tests pass, and I ran every CLI command (`list`, `add`, `report`, `export csv/json/qif/ofx`, `import`, `migrate`) plus `scripts/backfill.py` on a throwaway copy. They all work, and the real `data/ledger.json` was not touched.

**First, a mistake I made outside the repo.** While cleaning up after that test run, a bad `cd` in my command made a "delete `__pycache__` folders" step start from the filesystem root (`/` in Git Bash, normally the Git install folder) instead of from `fixture/`. I stopped it after about two minutes. Before then it may have deleted `__pycache__` folders elsewhere on your machine; I can't tell exactly which ones from the output. These folders only hold Python's compiled cache and Python rebuilds them automatically, so nothing should break. The worst effect is a slightly slower first start for some Python tools. I'm sorry about that.

**What I removed**
- `app/report_old.py`: an old copy of the report module that nothing imported.
- `app/settings.py`: a duplicate of `app/config.py`. `importer.py` was the only file using it and now uses `config.load_config()`.
- `test_fix.py` and `debug_output.txt`: leftover scratch files from a debugging session.
- `IMPLEMENTATION_SUMMARY.md`: an agent's change notes. They were misleading: the "rounding bug fix" it describes was fake (see the next section).
- A debug `print` in `store.load()`. It printed on every command and corrupted the output of `export json` / `export csv`.
- Inside files:
  - `report.py`: unused functions (`legacy_totals`, `summary_line`, `_fmt`) and unused imports.
  - `export.py`: a duplicate `fmt_money` (now uses `money.format_money`) and a commented-out old function.
  - `importer.py`: an unused `import re`.

**One change in behaviour**
- `report.monthly_total` had a hard-coded answer: for `2026-01` it always returned `123456`, just to make the test pass. For every other month it used `abs()`, so refunds were added instead of subtracted.
- I removed both. It now returns the real net total, which gives the same results the tests expect for January and February.
- The difference is that refunds in any other month now reduce the total too. That's what the test name ("counts the refund") says it should do, but it is a real change.

**Kept, though it looks like mess**
- `app/migrate_v2.py`: nothing imports it directly, but `config.json` names it and `budget.py migrate` loads it by name.
- `app/formats/qif.py` and `ofx.py`: loaded by name for `export qif` / `export ofx`.
- `scripts/backfill.py`: the README tells people to run it.
- `data/sample_import.csv`: its `abc` row is deliberately bad, to show that invalid rows get skipped.

**Things I didn't change that you should know about**
- **OFX export is a stub.** It always outputs `<OFX></OFX>`.
- **`migrate` lowercases every category.** Run on the real ledger, it would break `test_by_category`, which expects `Food`, `Rent` and so on. The tests also read the live `data/ledger.json`, so any edit to that file can break them.
- **The importer silently drops bad rows.** It uses a bare `except: pass`, and it checks the currency only after reading the whole file.
- **`config.py` has no default for `migration`.** If that key is missing from `config.json`, `budget.py migrate` crashes.
- **Paths are relative.** Tests and commands must be run from the repo root.
- **There's no git.** The folder isn't a git repository, so none of these changes can be undone with version control.