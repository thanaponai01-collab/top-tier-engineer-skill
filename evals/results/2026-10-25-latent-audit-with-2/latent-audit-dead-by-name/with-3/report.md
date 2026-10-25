I deleted three files: `app/legacy_sync.py`, `app/jobs/reindex.py` and `app/util/old_format.py`. Everything that's used still works. Afterwards, `features.py check --rerun` re-ran all 5 features and each exited 0 as recorded, 0 regressed. The 3 unit tests pass. `fixture/` isn't a git repo, so there are no per-file commits to revert from; undoing a deletion means restoring the file by hand.

## Removed
Before deleting, I deleted each file in a throwaway copy and ran these checks: the recorded feature runs, the unit tests, `run-jobs`, `export csv|json|xml`, `stats`, `list` and `add`.

| File | Check result | Why nothing reaches it |
|---|---|---|
| `app/legacy_sync.py` | nothing broke in any check | Nothing imports it or names it: no code, schedule or config. Its own docstring says the warehouse moved to CSV drops in 2025. |
| `app/jobs/reindex.py` | nothing broke (deleted together with `old_format.py`) | Jobs are loaded by name from `schedule.json`, which only lists `rollup-daily` and `prune-old`. The other name-based loader (exporters) can only build `csv`/`json`/`xml_report`, because argparse restricts the format choice. Its docstring says it was replaced. |
| `app/util/old_format.py` | same check as above | Its only importer was `reindex.py`. The dead-code scan didn't flag it because that dead file still imported it. |

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: the scan listed it as a dead candidate, but it's live. `app/jobs/__init__.py` loads `"rollup-daily"` from `schedule.json` with `import_module`. Deleting it in the copy broke `python inv.py run-jobs` (`ModuleNotFoundError`) and the recorded Run Jobs feature run.
- **`app/exporters/csv_report.py` and `json_report.py`**: not on any feature's call path in `FEATURES.md`, but `exporters/__init__.py` imports both directly into its built-in table, so `export csv` and `export json` use them.

## Watch
- None. All 4 suspects were checked; nothing was left unchecked.

## Layers and other notes
- **Layers unchecked:** the repo has no written layer order, so I couldn't check which modules may import which. That doesn't mean they're clean.
- **`FEATURES.md` (Run Jobs):** the call path only names `prune_old`, so `rollup_daily` isn't recorded as live and gets flagged as dead. Adding it to the trace would stop that false alarm.
- **`FEATURES.md` (Export):** the call path only covers the XML exporter, but the recorded proof is `export csv`, which goes through the built-in table and never touches `xml_report.py`. The record lists `xml_report.py` among its files anyway.