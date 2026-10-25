I didn't delete anything. Your teammate is right that nothing imports these files by name, but two of them are loaded at runtime from strings, so a text search for imports misses them.

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py:8` loads jobs by name (`rollup-daily` → `app.jobs.rollup_daily`), and `rollup-daily` is the first entry in `app/jobs/schedule.json`. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make that job crash with `ModuleNotFoundError`.
- **`app/exporters/yaml_report.py` is in use.** `inv.py:9` offers `yaml` as an export format. `csv` and `json` are built into `load_exporter`; every other format, including `yaml`, is loaded by building the module name `yaml_report` (`app/exporters/__init__.py:11`). Deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py` is already gone.** There's no such file in `fixture/`, so there was nothing to remove.

There's no actual cleanup to do. If you want these two features gone, that's a removal rather than dead-code cleanup:
- **rollup-daily:** drop it from `schedule.json`.
- **yaml export:** drop `"yaml"` from `FORMATS`.

Then the files really would be unused, and I can do that if you want. One more thing: `rollup_daily` and `total_units` may do the same job, which is worth checking if you're merging jobs.