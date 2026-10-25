I deleted three dead files and kept one that only looked dead. After the deletions, all 5 features still run as recorded (`features.py check --rerun` shows 0 broken), the 3 unit tests pass, and `run-jobs` plus all three export formats still give the same output.

## Removed
Before each deletion I deleted the file in a throwaway copy and ran the recorded feature runs, the unit tests and every app command: `run-jobs`, `export csv`, `export json`, `export xml`, `stats`, `list` and `add`. Each result was `DELETE-CHECK: nothing-breaks(...)`.

| File | Why nothing reaches it |
|---|---|
| `app/legacy_sync.py` | Nothing imports it and no config or schedule names it. Its own docstring says the warehouse moved off this API in 2025. |
| `app/jobs/reindex.py` | Jobs are loaded by name from `app/jobs/schedule.json`, and that file only lists `rollup-daily` and `prune-old`. Its docstring says search moved to a linear scan. |
| `app/util/old_format.py` | Only `reindex.py` imported it, so it was dead along with that file. The scan didn't flag it because that dead import hid it. |

The folder isn't a git repo, so I deleted the files directly instead of making one commit per file. Nothing else referred to them, so there were no tests or config to remove with them.

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: no file imports it, but `schedule.json` lists it as `rollup-daily` and the job runner loads it by that name. Deleting it in the copy broke `run-jobs` with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: also has no direct import. `load_exporter` builds the module name from the format the user picks, so `export xml` loads it. The feature map already marks it as live.
- **`csv_report.py` / `json_report.py`**: these are used through the `BUILT_IN` table in `app/exporters/__init__.py`.

## Watch
None. All 4 suspects were checked.

## Layers and bugs noted
- **Layers: unchecked.** The repo doesn't write down a layer order, so I didn't make one up.
- **Bug:** `app/exporters/__init__.py:11`: `load_exporter` would import any module named `<fmt>_report`. Today only the argparse choices in `inv.py` stop bad input, so any other caller of `load_exporter` would get an unclear `ModuleNotFoundError` instead of a proper error. I noted this and didn't change it.