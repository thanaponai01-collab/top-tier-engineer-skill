I didn't delete anything. Two of the three files are still in use, and the third doesn't exist.

The teammate's grep found no imports because both packages load modules by building the module name as a string at runtime:

- **`app/jobs/rollup_daily.py` is in use.** `app/jobs/__init__.py:8` turns a job name into a module (`rollup-daily` → `rollup_daily`), and `app/jobs/schedule.json` lists `"rollup-daily"` first. The README says the nightly cron runs `python inv.py run-jobs`, so this job runs every night. Deleting the file would crash that run on its first job, and the rest of the jobs wouldn't run either.
- **`app/exporters/yaml_report.py` is in use.** `inv.py` accepts `"yaml"` as an export format, and `app/exporters/__init__.py:11` loads it as `yaml_report`. Deleting the file would make `python inv.py export yaml` fail.
- **`app/jobs/vacuum_store.py` doesn't exist** in `fixture/`, and nothing mentions `vacuum_store` anywhere. It may already have been removed, or the name is wrong.

If you do want to retire rollup-daily or the YAML export, it's a small change: remove `"rollup-daily"` from `schedule.json` or `"yaml"` from `FORMATS` in `inv.py`, then delete the file. That turns off a feature that's currently live, though, so check with whoever owns the nightly jobs or the YAML export first. Tell me which, if either, and I'll make the change.