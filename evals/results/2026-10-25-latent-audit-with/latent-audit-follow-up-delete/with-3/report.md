I didn't delete anything. Two of the three files are definitely still used, and the third may be. Nothing imports them with a plain `import` statement, but the code loads modules by building their names from strings at runtime, so a search for imports doesn't find them:

- **`app/jobs/rollup_daily.py`: still used.** `app/jobs/schedule.json` lists `"rollup-daily"` first. `run_all` in `app/jobs/__init__.py:8` turns that name into `app.jobs.rollup_daily` and loads it. If you delete the file, `inv run-jobs` crashes at its first job (`ModuleNotFoundError`), and none of the jobs after it run.
- **`app/exporters/yaml_report.py`: still used.** `inv.py:9` lists `"yaml"` as an export format. `load_exporter` in `app/exporters/__init__.py:11` loads `app.exporters.yaml_report` for it. If you delete the file, `inv export yaml` crashes.
- **`app/jobs/vacuum_store.py`: probably unused.** It isn't in `schedule.json` and nothing else mentions it. But `inv run-job vacuum-store` can still run it, because `run-job` accepts any job name. Someone might run it by hand or from a cron job or script outside this repo, and I can't check that from here.

My suggestion:
- Keep `rollup_daily.py` and `yaml_report.py`, unless you also want to drop the daily rollup from the schedule and the YAML export from the CLI. That's a feature removal, not a dead-code cleanup.
- Delete `vacuum_store.py` (and its `.pyc` in `__pycache__`) once you've confirmed nobody runs `vacuum-store` manually. If you already know that, tell me and I'll delete it now.