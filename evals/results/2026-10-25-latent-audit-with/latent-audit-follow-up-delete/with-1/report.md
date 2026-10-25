I deleted only `vacuum_store.py`. The other two are loaded at runtime by name, so a plain import search misses them. Deleting them would break things in production.

- **`app/jobs/rollup_daily.py` — still in use, kept.** `app/jobs/__init__.py:8` loads jobs by name (`import_module(f"{__name__}.{name.replace('-', '_')}")`). `"rollup-daily"` is the first entry in `app/jobs/schedule.json`. The README says the nightly cron runs `python inv.py run-jobs`, which goes through that schedule. If this file were gone, the nightly run would crash on its very first job, and the other 13 jobs wouldn't run either.
- **`app/exporters/yaml_report.py` — still in use, kept.** `inv.py:9` offers `"yaml"` as an export format. `app/exporters/__init__.py:11` loads it as `f"{fmt}_report"`, so `inv export yaml` depends on it.
- **`app/jobs/vacuum_store.py` — dead, so I deleted it.** It isn't in `schedule.json`, and nothing else mentions it. The only way to reach it was typing `inv run-job vacuum-store` by hand. I also removed its cached `.pyc` in `__pycache__`.

This folder isn't a git repository, so the deleted file can't be recovered from history. It was a two-line stub that returned `'vacuumed'`.

If you still want rollup-daily or YAML export removed, that means retiring a feature, not cleaning up dead code. I can do it: drop `rollup-daily` from `schedule.json` and `"yaml"` from `FORMATS`, then delete the files. Check with whoever owns the nightly job and the export users first.