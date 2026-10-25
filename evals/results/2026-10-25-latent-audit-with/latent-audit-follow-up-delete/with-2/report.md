I deleted only `app/jobs/vacuum_store.py`. The other two files are still in use: they're loaded by a name built at runtime, so a search for imports doesn't find them.

**Kept, because deleting them would break things:**
- **`app/jobs/rollup_daily.py`**: `rollup-daily` is the first entry in `app/jobs/schedule.json`. `run_all()` in `app/jobs/__init__.py:8` turns that name into `app.jobs.rollup_daily` and loads it. The README says the nightly cron runs `python inv.py run-jobs`, so deleting this file would make that job crash every night.
- **`app/exporters/yaml_report.py`**: `inv.py:9` lists `"yaml"` as an export format. `load_exporter()` in `app/exporters/__init__.py:11` loads `app.exporters.yaml_report` for it, so `inv.py export yaml` would fail without the file.

**Deleted:**
- **`app/jobs/vacuum_store.py`**: it isn't in the schedule, nothing references it, and it never had a cached compiled copy, which suggests it has never been run. All it did was `return 'vacuumed'`. The only way to reach it was typing `inv.py run-job vacuum-store` by hand. This folder isn't a git repo, so nothing can be restored automatically. If someone needs the file back, it was just:
  ```python
  def run(items):
      return 'vacuumed'
  ```

If you do want rollup-daily or YAML export gone, that means also removing `rollup-daily` from `schedule.json` and `"yaml"` from `FORMATS` in `inv.py`. That would be a decision to drop features, though, not a dead-code cleanup, so I left it for you to decide.