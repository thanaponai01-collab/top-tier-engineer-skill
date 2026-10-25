I didn't delete anything. None of the three files is actually safe to remove. The teammate is right that nothing imports them by name, but two of them get loaded at runtime from a string, so a grep for imports misses them. The third doesn't exist.

- **`app/exporters/yaml_report.py` is in use.** `"yaml"` is one of the allowed formats in `inv.py:9`, and `load_exporter` in `app/exporters/__init__.py:11` loads it with `import_module(f"{__name__}.{fmt}_report")`. Deleting it would make `python inv.py export yaml` crash with `ModuleNotFoundError`.
- **`app/jobs/rollup_daily.py` is in use.** `"rollup-daily"` is the first entry in `app/jobs/schedule.json:3`. `run_all` turns that name into `app.jobs.rollup_daily` and imports it. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make that run crash on its very first job, before any of the other jobs run.
- **`app/jobs/vacuum_store.py` doesn't exist.** It isn't in `app/jobs/` and there's no compiled copy of it either. It was either removed already or the name is wrong.

This also means the cleanup can't happen today as planned. If you want to retire the YAML export or the daily rollup, the options are:
1. Remove `"yaml"` from `FORMATS` in `inv.py`, then delete `yaml_report.py`.
2. Remove `"rollup-daily"` from `schedule.json`, then delete `rollup_daily.py`. This changes what the nightly cron does, so check with whoever relies on that output first.

I can make either change if you confirm. It would be worth telling your teammate that the exporters and jobs are loaded by name, so "nothing imports them" won't catch them.