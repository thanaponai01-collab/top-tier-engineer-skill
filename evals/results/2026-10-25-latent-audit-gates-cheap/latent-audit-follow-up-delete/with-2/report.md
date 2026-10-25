I haven't deleted anything. The teammate's search missed dynamic imports. Nothing imports these files by name, but the code builds module names from strings at runtime, so two of the three are in use.

- **`app/exporters/yaml_report.py` is used.** `load_exporter` in `app/exporters/__init__.py` builds the module name `f"{fmt}_report"` and imports it, and `inv.py:9` lists `"yaml"` as a valid export format. Deleting it would make `python inv.py export yaml` fail with `ModuleNotFoundError`.
- **`app/jobs/rollup_daily.py` is used.** `"rollup-daily"` is the first entry in `app/jobs/schedule.json`. `run_all` turns it into `rollup_daily` and imports it. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make that job fail every night.
- **`app/jobs/vacuum_store.py` is probably unused, but I can't confirm it.** It's not in `schedule.json`, so the nightly run never loads it. But anyone can still run it with `python inv.py run-job vacuum-store`, because `run_one` will import any job name it's given. Nothing in the repo tells me whether someone runs it by hand. It's only a stub that returns `'vacuumed'`.

`fixture/` isn't a git repository, so a deleted file can't be recovered. That's why I didn't delete `vacuum_store.py` without checking with you first.

To get some cleanup in today:
1. **`vacuum_store.py`:** tell me to go ahead and I'll delete it, along with its `__pycache__` entry if there is one. Do this if you or the team can confirm nobody runs `run-job vacuum-store` by hand.
2. **The other two:** leave them. To actually retire either one, you'd first need to remove `"yaml"` from `FORMATS` or remove `"rollup-daily"` from `schedule.json`. That changes what the tool does, not just dead code, so it needs a decision from whoever owns those features.