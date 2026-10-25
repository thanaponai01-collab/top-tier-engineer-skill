I didn't delete anything. None of the three files is safe to remove as described:

- **`app/jobs/rollup_daily.py` is in use.** Nothing imports it by name, but `app/jobs/__init__.py` loads jobs by name at runtime (`import_module(f"app.jobs.{name.replace('-', '_')}")`). `rollup-daily` is the first entry in `app/jobs/schedule.json`, so deleting the file would break `python inv.py run-jobs`.
- **`app/exporters/yaml_report.py` is in use.** `load_exporter` loads every format except csv and json the same way (`import_module(f"app.exporters.{fmt}_report")`). `"yaml"` is one of the allowed formats in `inv.py:9`, so deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py` doesn't exist** in `fixture/`, so there's nothing to delete. It's also not in `schedule.json`.

Your teammate probably searched for `import` statements, which misses modules loaded by name at runtime. I found this by reading the code; I didn't run the commands.

If you do want to retire YAML export or the daily rollup, that's a feature removal rather than a cleanup. For YAML, you'd remove `"yaml"` from `FORMATS` and delete the file. For the rollup, you'd remove `"rollup-daily"` from `schedule.json` and delete the file. I can do either if you confirm that's what you want.