I didn't delete anything. Two of the three files are still in use, and the third doesn't exist.

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py` loads jobs by name from `app/jobs/schedule.json`, and `"rollup-daily"` is the first job in that list. Deleting the file would break `python inv.py run-jobs`, which the README says the nightly cron runs.
- **`app/exporters/yaml_report.py` is in use.** `load_exporter()` in `app/exporters/__init__.py` builds the module name `{fmt}_report` at runtime, and `inv.py` accepts `yaml` as an export format. Deleting it would make `python inv.py export yaml` fail.
- **`app/jobs/vacuum_store.py` isn't in `fixture/`.** It's not in the file listing and `cat` can't find it, so either someone already removed it or the path is wrong.

Your teammate's "nothing imports them" is true in the narrow sense, since no file has an `import` statement for these modules. But both packages load modules by name at runtime, so a search for imports won't find their callers.

If you still want this cleanup, the real work is retiring features rather than removing dead files:
- **rollup-daily:** take it out of `schedule.json` and confirm nobody relies on that nightly output.
- **yaml export:** remove `"yaml"` from `FORMATS` in `inv.py`.

Tell me if you want either one, and I'll make the change and run the tests and CLI commands to check it.