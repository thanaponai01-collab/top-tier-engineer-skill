I deleted three dead files. Every command still works: all CLI commands (`--help`, `list`, `stats`, `export csv/json/xml`, `run-jobs`, and `add` in a throwaway copy), the unit tests, and the feature map check (`check --rerun`: 0 broken, 0 regressed). The audit helper's gate reports `LATENT-GATE: done`.

**Removed** (none of them loaded during any command or test run, and nothing in the repo names them):
- `app/legacy_sync.py`: pushed stock to the old warehouse API. Its own docstring says the warehouse moved to CSV drops in 2025, and nothing imports it.
- `app/jobs/reindex.py`: a job that isn't listed in `app/jobs/schedule.json`, so the job runner never loads it. Its docstring says search moved to a linear scan.
- `app/util/old_format.py`: only `reindex.py` used it, so it went with it.

**Kept, though they looked dead:**
- `app/jobs/rollup_daily.py`: no file imports it, but `schedule.json` lists `"rollup-daily"` and the job runner loads it by name. `run-jobs` prints its output.
- `app/exporters/xml_report.py`: no file imports it, but `load_exporter` builds its module name from the format the user asks for, so `export xml` loads it.
- `app/jobs/prune_old.py`: loaded the same way as `rollup_daily.py`, through `schedule.json`.
- `app/exporters/json_report.py` and `app/util/dates.py` are imported normally, so they are plainly in use.

**Notes:**
- I didn't check whether code imports across layers in the wrong direction, because the repo doesn't declare a layer order.
- `fixture/` isn't a git repo, so nothing was committed. The audit records are in `.latent/` (`snapshot.json`, `inventory.json`), which the skill says to commit along with the deletions.
- `items.json` is byte-for-byte unchanged.