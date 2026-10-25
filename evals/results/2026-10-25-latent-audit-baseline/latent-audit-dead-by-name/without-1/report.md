I deleted three dead files. Everything still runs: the 3 unit tests pass, all five commands (`add`, `list`, `export`, `stats`, `run-jobs`) were re-run, and `features.py check --rerun` reports nothing broken or regressed. I ran `features.py prove --again`, as `AGENTS.md` asks, so the recorded runs are refreshed.

**Removed**
- `app/legacy_sync.py`: sends stock to the old warehouse API. Nothing imports it, and its own docstring says the warehouse switched to CSV drops in 2025.
- `app/jobs/reindex.py`: a job that isn't listed in `app/jobs/schedule.json`, which is the only way jobs get run. Its docstring says it was replaced.
- `app/util/old_format.py`: only `reindex.py` used it, so it went with it.

**Kept, though they look dead** (nothing imports them by name, but they are loaded by name while the program runs):
- `app/exporters/xml_report.py`: `load_exporter` imports `<fmt>_report` for any format other than csv and json, so `inv.py export xml` uses this file. I ran it and the output is correct.
- `app/jobs/rollup_daily.py` and `app/jobs/prune_old.py`: `run_all` loads these from the names in `schedule.json` (`rollup-daily` → `rollup_daily`). Both show up in `inv.py run-jobs`.
- `app/util/dates.py` `age_days`: used by `prune_old.py`.
- `app/jobs/schedule.json`: data rather than code, but deleting it would break `run-jobs`.