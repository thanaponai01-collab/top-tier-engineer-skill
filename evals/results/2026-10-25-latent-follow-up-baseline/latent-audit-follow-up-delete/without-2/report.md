I didn't delete anything. Your teammate is right that nothing imports these files by name, but the code loads them dynamically at runtime from strings, so they aren't dead.

**`app/jobs/rollup_daily.py` is in use.** `app/jobs/schedule.json` lists `"rollup-daily"` first. `app/jobs/__init__.py` loads each scheduled job with `import_module(f"{__name__}.{name.replace('-', '_')}")`. That turns `rollup-daily` into `app.jobs.rollup_daily`. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make that run fail on its first job with `ModuleNotFoundError`.

**`app/exporters/yaml_report.py` is in use.** In `inv.py`, `FORMATS` includes `"yaml"`. For any format that isn't csv or json, `load_exporter` in `app/exporters/__init__.py` runs `import_module(f"{__name__}.{fmt}_report")`. Deleting the file would break `python inv.py export yaml`.

**`app/jobs/vacuum_store.py` doesn't exist.** There's nothing to delete, and nothing in the repo mentions "vacuum".

A search for import statements won't find these uses, which is probably how they got flagged. The xml, md, html and tsv exporters are loaded the same way.

If you do want to retire rollup-daily or YAML export, I can do it properly:
- **rollup-daily:** remove its entry from `schedule.json` along with the file.
- **YAML export:** remove `"yaml"` from `FORMATS` in `inv.py` along with the file.

Either way, check with whoever relies on the nightly rollup or YAML exports before removing them.