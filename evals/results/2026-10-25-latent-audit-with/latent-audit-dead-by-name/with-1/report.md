I deleted two files and kept one that looks dead but couldn't be proven dead. After the deletions, the five features (add, list, export, stats, run-jobs) and the unit tests all still pass.

## Removed
- **`app/jobs/reindex.py`**: no job list or import reaches it. `run_all` only loads the jobs named in `app/jobs/schedule.json` (`rollup-daily`, `prune-old`), and `reindex` isn't one of them. Its own docstring says search moved to a linear scan. The delete-check passed: `nothing-breaks` with `run-jobs` (the only command that could load a job), every export format, `stats`, `list`, the unit tests and the five recorded feature runs.
- **`app/util/old_format.py`**: the only thing that imported it (`normalize`) was `reindex.py`. Deleting both files together also came back `nothing-breaks` on the same checks.

`fixture/` isn't a git repo, so there are no commits; the two deletions are in the working tree.

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: no code imports it by name, but `schedule.json` lists it as `rollup-daily` and `run_all` turns that into `rollup_daily`. Deleting it makes `inv.py run-jobs` fail (`ModuleNotFoundError: No module named 'app.jobs.rollup_daily'`).
- **`csv_report.py`, `json_report.py`, `xml_report.py`**: the first two are imported directly. `xml_report` is loaded by name (`import_module(f"...{fmt}_report")`) when you run `export xml`.

## Watch (kept, your call)
- **`app/legacy_sync.py`** (`push()` to `http://warehouse.internal/api/v1/stock`): nothing in the repo reaches it. Deleting it broke nothing, but no command here would ever have loaded it, so that's not proof. If it still runs, it's from outside this repo, like a cron job or another service doing `from app.legacy_sync import push`. Its docstring says the warehouse moved to CSV drops in 2025, so it's very likely dead. Check there are no outside callers, then delete it.
- All suspects were checked; none were skipped.

## Layers and bugs
- **Layers weren't checked**: the repo doesn't say which modules may import which. If you give me that order, I can check for imports that break it.
- **Bugs noticed along the way:**
  - `app/jobs/__init__.py:12`: a job name in `schedule.json` with no matching module crashes the whole `run-jobs` command rather than just skipping that job.
  - `app/exporters/__init__.py:11`: an unknown format name is used as part of a module name to import. The CLI only accepts csv, json or xml, but other code calling it isn't protected.