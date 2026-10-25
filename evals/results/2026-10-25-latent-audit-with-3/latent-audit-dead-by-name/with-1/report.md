I deleted three files. Everything still works: the feature check passes with all 5 features re-run as recorded, the unit tests pass, and `run-jobs` and `export xml` give the same output as before.

## Removed
Before each deletion I deleted the file in a throwaway copy and ran the unit tests, the recorded feature runs, and every app command: `run-jobs`, `export csv`, `export json`, `export xml`, `stats`, `list`, `add`. Nothing broke.

- **`app/legacy_sync.py`**: nothing imports it, and neither of the app's two name-based loaders can reach it (one only loads `app.exporters.*_report`, the other only `app.jobs.*`). No config or schedule names it. Its own docstring says the warehouse switched to CSV drops in 2025.
- **`app/jobs/reindex.py`**: jobs are only ever loaded by name from `app/jobs/schedule.json`, and `reindex` isn't listed there. Its docstring says it was replaced.
- **`app/util/old_format.py`**: only `reindex.py` used it, so I removed the two together.

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: no import names it, but `schedule.json` lists it as `"rollup-daily"` and `run_all` loads it by name. A test deletion confirmed it: `run-jobs` failed with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: `load_exporter` builds the module name from the format, so `export xml` loads it by name.
- **`app/jobs/prune_old.py`**: listed in `schedule.json` as `"prune-old"`.
- **`app/exporters/csv_report.py` and `json_report.py`**: used through the `BUILT_IN` table in `exporters/__init__.py`.
- **`app/util/dates.py`**: used by `store.py` and `prune_old.py`.

## Not checked
- **Watch list:** empty. Every suspect got a definite keep-or-delete result.
- **Layer rules:** not checked. The repo doesn't write down which parts of the code may import which, so I can't say whether that's clean.
- **Possible bug:** `app/jobs/prune_old.py:5` will crash if an item has no `added` date. `store.add` always sets one, but older entries in `items.json` might lack it. I didn't follow this up.

The folder isn't a git repo, so I couldn't commit each deletion separately. If you need the files back, they'll have to be restored from your own copy.