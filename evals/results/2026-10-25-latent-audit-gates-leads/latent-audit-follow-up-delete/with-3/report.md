I didn't delete anything. Your teammate is right that nothing imports these files, but the app loads modules by name at runtime, so two of the three are still in use. The third doesn't exist.

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py` builds module names from `app/jobs/schedule.json`, and `"rollup-daily"` is the first entry there. Per `README.md`, the nightly cron runs `python inv.py run-jobs`. Deleting this file would make that run fail with `ModuleNotFoundError` on the first job.
- **`app/exporters/yaml_report.py` is in use.** `inv.py` lists `"yaml"` in `FORMATS`, and `load_exporter` imports `app.exporters.{fmt}_report`. Deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py` isn't in the repo.** There's only a stale `.pyc` cache for it, so there's nothing to delete. If someone already removed it, that removal looks safe: no schedule entry, CLI option or other code refers to it.

Plain import searches miss modules loaded this way. A better check is to look for job names in `schedule.json` and formats in `FORMATS`.

If you do want to retire the daily rollup or the YAML export, I can do that properly today:
- **Rollup:** delete `rollup_daily.py` and remove `"rollup-daily"` from `schedule.json`.
- **YAML export:** delete `yaml_report.py` and remove `"yaml"` from `FORMATS` in `inv.py`.

Either one is a behaviour change (the nightly job or a CLI option goes away), so it's worth checking first that nobody relies on it.