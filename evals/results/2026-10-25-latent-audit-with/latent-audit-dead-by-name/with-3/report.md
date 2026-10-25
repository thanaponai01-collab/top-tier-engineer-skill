I deleted 3 files. Everything that's used still works: the recorded feature runs (`features.py check --rerun`) give 5/5 features ok and 0 regressed, the unit tests pass, and `run-jobs` and `export csv/json/xml` all give the same output as before.

## Removed
Each deletion was first tried in a throwaway copy while running `run-jobs`, `export csv`, `export json`, `export xml`, `stats`, `list`, the unit tests and the recorded feature runs. All three came back `DELETE-CHECK: nothing-breaks(...)`.

- **`app/jobs/reindex.py`**: jobs only load if their name is listed in `app/jobs/schedule.json`, and that file lists only `rollup-daily` and `prune-old`. Nothing else in the repo mentions `reindex`. Its own docstring says it was replaced.
- **`app/util/old_format.py`**: the only thing that imported it was `reindex.py`. I tested it deleted together with `reindex.py`.
- **`app/legacy_sync.py`**: nothing in the repo uses it, not by import, not by name, and no config, CLI command or test refers to it. Its docstring says the warehouse API it calls was retired in 2025. One caveat: a check inside this repo can't see callers outside it. If anything external imported `app.legacy_sync.push`, check that before you rely on this deletion.

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: the audit tool listed it as dead, but `schedule.json` lists `"rollup-daily"`, and `app/jobs/__init__.py` turns that into an import of `app.jobs.rollup_daily` at run time. Deleting it in the copy broke `inv.py run-jobs` with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: nothing imports it directly. `load_exporter` builds the name `{fmt}_report` and imports it at run time, so it's what `export xml` uses.

## Watch
- Nothing else is open. All 3 module candidates and the 1 unused function the tool reported (`push`) were checked; none were left unchecked.

## Not checked / noted
- **Layers not checked.** The repo doesn't write down a layer order, so there was nothing to check against. That means unchecked, not clean.
- `FEATURES.md` "Run Jobs": the trace names only `prune_old.py`, though `rollup_daily.py` also runs through `schedule.json`. Adding it to the trace would keep the next audit from flagging it again.
- `FEATURES.md` "Export": the status says both `export xml` and `export csv` were run, but `.features/export.json` only records `export csv`. `json_report.py` and `csv_report.py` aren't in the map either.