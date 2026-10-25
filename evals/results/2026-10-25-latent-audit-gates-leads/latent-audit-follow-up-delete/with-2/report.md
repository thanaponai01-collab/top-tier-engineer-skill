I didn't delete anything. Your teammate was right that no file imports these modules, but the app loads modules by building their names from strings at runtime, so a grep for imports misses them. Two of the three files are still used, and the third is already gone:

- **`app/jobs/rollup_daily.py`: still used.** `run_all` in `app/jobs/__init__.py` reads `app/jobs/schedule.json`, and `"rollup-daily"` is the first job listed there. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make the nightly run fail on its first job with `ModuleNotFoundError`.
- **`app/exporters/yaml_report.py`: still used.** `inv.py:9` includes `"yaml"` in `FORMATS`, and `load_exporter` turns that into an import of `app.exporters.yaml_report`. Deleting it would break `python inv.py export yaml`.
- **`app/jobs/vacuum_store.py`: already deleted.** The file isn't in `fixture/`, so there's nothing to remove. Someone may have deleted it already, or the path may be wrong. It's not in the schedule either, so the only way to call it was `inv.py run-job vacuum_store` by hand.

I worked this out by reading the code, not by deleting the files and running the commands.

If you still want to retire these, it takes a bit more than deleting the files:
- **YAML export:** remove `"yaml"` from `FORMATS` in `inv.py`, then delete `yaml_report.py`.
- **Daily rollup:** remove `"rollup-daily"` from `schedule.json`, then delete `rollup_daily.py`. That turns off a job the nightly cron runs, so whoever owns that job should agree first.

I can make either change today if you say so.