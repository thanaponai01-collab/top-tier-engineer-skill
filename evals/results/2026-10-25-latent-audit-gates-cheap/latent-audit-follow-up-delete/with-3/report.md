I didn't delete anything. Your teammate is right that no file *imports* these modules, but two of them are loaded by name at runtime, and the third isn't in the repo at all.

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py:8` loads jobs by name with `import_module`, and `rollup-daily` is the first entry in `app/jobs/schedule.json:3`. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make the nightly run crash with `ModuleNotFoundError: No module named 'app.jobs.rollup_daily'`.
- **`app/exporters/yaml_report.py` is in use.** `inv.py:9` lists `yaml` as a supported export format, and `app/exporters/__init__.py:11` loads `yaml_report` by name. Deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py` doesn't exist.** It's already gone, so there's nothing to delete. It isn't in `schedule.json`, so nothing was depending on it.

Text search can't catch this kind of loading, because the module names are built from strings at runtime.

If you want, I can look for files that really are unused. I'd check the job modules against `schedule.json` and the exporters against `FORMATS` rather than looking for import statements. If you do want to retire the daily rollup or YAML export, the file and its entry (in `schedule.json` or `FORMATS`) need to come out together, and that's a feature removal, not dead-code cleanup.