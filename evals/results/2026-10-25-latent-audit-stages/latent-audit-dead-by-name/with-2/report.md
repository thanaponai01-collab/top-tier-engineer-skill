I deleted 3 files. The audit's final check (`LATENT-GATE: done`) passes, and every command that loads code still passes after the deletions: all five `inv.py` commands, all three export formats, `run-jobs`, `--help`, the unit tests and the features map's recorded runs. `items.json` was not modified.

**Removed: never loaded by any command and not mentioned anywhere else in the repo**
- `app/legacy_sync.py`: pushed stock to the old warehouse API. Its docstring says the warehouse moved to CSV drops in 2025. Nothing imports it.
- `app/jobs/reindex.py`: the old search-index job. Its docstring says it was replaced. It isn't listed in `app/jobs/schedule.json`, so the job runner never loads it.
- `app/util/old_format.py`: only `reindex.py` used it, so it became dead once that was gone.

If something outside this repo imports `app.legacy_sync`, such as a cron line on a server, it will now fail. Nothing in the repo points to such a caller.

**Kept, though they looked dead**
- `app/jobs/rollup_daily.py`: no import names it, but `schedule.json` lists `rollup-daily`. `app/jobs/__init__.py:11` turns that name into a module name and loads it when the jobs run. The `run-jobs` run confirmed it loads.
- `app/jobs/prune_old.py`: loaded the same way through `schedule.json`, and `FEATURES.md` names it.
- `app/exporters/xml_report.py`: no import names it either, but `load_exporter` in `app/exporters/__init__.py` builds the module name for any format other than CSV or JSON. `inv.py export xml` uses it.

**Not done**
- I didn't check layer violations (imports that cross the app's layers the wrong way) because the repo doesn't declare its layers.
- The repo isn't under git, so I committed nothing. The audit's records are in `fixture/.latent/`; the skill says to commit that folder together with the deletions.