I deleted only `app/jobs/vacuum_store.py`. Your teammate is right that no file has an `import` line for these three, but two of them are still used: the app loads modules by name at runtime.

- **`app/jobs/rollup_daily.py` is in use. I kept it.** `app/jobs/__init__.py:8` loads jobs by name from `app/jobs/schedule.json`, and `"rollup-daily"` is the first entry there. The README says the nightly cron runs `python inv.py run-jobs`, and I ran that command: it prints `rollup-daily: 165 units across 3 lines`. Deleting the file would crash the nightly run at its first job.
- **`app/exporters/yaml_report.py` is in use. I kept it.** `inv.py:9` lists `"yaml"` as an export format, and `app/exporters/__init__.py:11` turns that into a load of `yaml_report`. `python inv.py export yaml` works now and would break without the file.
- **`app/jobs/vacuum_store.py` is deleted.** Nothing referenced it: no imports, not in the schedule, not in the README. One caveat: before the deletion, someone could still run it by hand with `inv.py run-job vacuum-store`. If anyone did that, the command will now fail.

After the deletion the 3 tests pass, and `run-jobs` and `export yaml` still work.

If you want `rollup_daily` and `yaml_report` gone too, the fix is bigger than deleting two files. Remove `"rollup-daily"` from `schedule.json` and `"yaml"` from `FORMATS` in `inv.py`, and check with whoever owns the nightly cron and the YAML export first. I can do that if you confirm.