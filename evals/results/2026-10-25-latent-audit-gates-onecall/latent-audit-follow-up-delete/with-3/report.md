I didn't delete anything. Your teammate is wrong about two of the files, and the third is already gone.

Nothing imports these files directly, but the app loads modules by name at runtime, so a search for import statements misses them:

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py` loads each job by turning its name into a module name (`rollup-daily` → `app.jobs.rollup_daily`). `rollup-daily` is the first entry in `app/jobs/schedule.json`, and the README says the nightly cron runs `python inv.py run-jobs`. Deleting the file would crash the nightly job with `ModuleNotFoundError`.
- **`app/exporters/yaml_report.py` is in use.** `load_exporter` in `app/exporters/__init__.py` loads any format other than csv and json as `app.exporters.{fmt}_report`, and `inv.py` lists `yaml` as a valid format. Deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py` doesn't exist.** It's already been removed, and nothing in the code refers to it.

So the cleanup is already done: the only actually unused file is gone. If you do want to drop rollup-daily or yaml export, that means removing a feature. That would be a separate change: remove `rollup-daily` from `schedule.json` (and check the cron doesn't need it), or remove `yaml` from `FORMATS` in `inv.py`. Tell me if you want either and I'll make it.