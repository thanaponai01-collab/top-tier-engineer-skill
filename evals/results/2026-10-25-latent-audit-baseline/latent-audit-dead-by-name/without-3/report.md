I deleted three files. After that, all five features still pass `features.py check --rerun` with nothing broken or regressed, and the 3 unit tests pass. I also ran `list`, `stats`, `run-jobs` and `export csv/json/xml` by hand and each one works. FEATURES.md didn't mention any of the deleted files, so it needed no edits.

**Removed:**
- **`app/legacy_sync.py`**: nothing imports it. It posted stock to the old warehouse API, and its own docstring says that was replaced by CSV drops in 2025.
- **`app/jobs/reindex.py`**: jobs only run if they're listed in `app/jobs/schedule.json`, and the list there is just `rollup-daily` and `prune-old`, so this one never ran. Its docstring says it was replaced.
- **`app/util/old_format.py`**: `reindex.py` was the only thing that used it.

**Kept, though they look unused at first glance:**
- **`app/exporters/xml_report.py`**: no code imports it by name, but `load_exporter` loads `<fmt>_report` from the format you ask for, so `inv.py export xml` needs it.
- **`app/jobs/prune_old.py` and `app/jobs/rollup_daily.py`**: also never imported by name. `run_all` loads them using the names in `schedule.json`, so `run-jobs` needs them.
- **`app/util/dates.py`**: `today` is used by `store.add`, and `age_days` by `prune_old`.
- **`app/util/text.py`**: `plural` is used by the `stats` summary.

This folder isn't a git repository, so there's no history to restore the deleted files from. If you might want them back, take them from another copy.