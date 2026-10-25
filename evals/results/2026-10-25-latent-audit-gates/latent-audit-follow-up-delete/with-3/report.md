I didn't delete anything. None of the three files is dead code. Nothing imports them by name, but the CLI loads modules from strings at runtime, so a plain import search misses them.

- **`app/exporters/yaml_report.py` is in use.** `inv.py:9` lists `"yaml"` as an export format, and `load_exporter` in `app/exporters/__init__.py` loads `f"{fmt}_report"` by name. Deleting it would make `python inv.py export yaml` crash with `ModuleNotFoundError`.
- **`app/jobs/rollup_daily.py` is in use.** `"rollup-daily"` is the first entry in `app/jobs/schedule.json`, and `run_one` turns that name into `app.jobs.rollup_daily` and imports it. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would crash the nightly run at its first job, and the other 13 jobs wouldn't run either.
- **`app/jobs/vacuum_store.py` doesn't exist.** There's no such file in `fixture/`, so there's nothing to delete. Either someone already removed it or your teammate was looking at a different copy of the repo.

If you do want to retire YAML export or the daily rollup, it takes more than deleting the file. You'd remove `"yaml"` from `FORMATS` in `inv.py`, or `"rollup-daily"` from `schedule.json`, together with the file. Since that changes what the CLI and the nightly cron do, it's your call, and I can make either change if you confirm.

The repo also has a `.latent/` folder with notes that reach the same verdicts. I checked the code myself rather than relying on those notes.