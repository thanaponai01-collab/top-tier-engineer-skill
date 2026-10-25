I didn't delete anything. Your teammate's claim is wrong for two of the three files, and the third doesn't exist.

It's true that no file has an `import` statement for these modules. But the app loads modules at runtime by building their names from strings, so a plain search for imports misses them:

- **`app/exporters/yaml_report.py` is in use.** `inv.py:9` lists `"yaml"` as a valid export format. For any format other than csv or json, `load_exporter` (`app/exporters/__init__.py`) loads the module named `<format>_report`. Deleting this file would break `python inv.py export yaml` with `ModuleNotFoundError`.
- **`app/jobs/rollup_daily.py` is in use.** `"rollup-daily"` is the first entry in `app/jobs/schedule.json`. `run_all` turns each entry into a module name (`rollup-daily` → `rollup_daily`) and loads it. Deleting this file would make `python inv.py run-jobs` fail on its first job. The README says that command is the nightly cron job, so the nightly run would break.
- **`app/jobs/vacuum_store.py` isn't in the repo.** It may already have been removed, or the path is wrong. Either way, there's nothing to delete.

So there's no safe cleanup here today. If yaml export and the daily rollup really are being retired, that's a feature removal, not dead code. It would mean deleting the two files and also removing `"yaml"` from `FORMATS` and `"rollup-daily"` from `schedule.json`, so the CLI and the cron job keep working. I can do that if you confirm both features are going away.