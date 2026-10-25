I deleted three files of dead code, and every command still works. The 3 unit tests pass, the features check is clean, and I ran `export xml`, `export json`, `stats` and `run-jobs` myself. I also re-recorded the feature proofs with `prove --again`, as AGENTS.md asks.

**Removed:**
- **`app/legacy_sync.py`**: nothing imports it. It pushed stock to the old warehouse API, and its own docstring says the warehouse moved to CSV drops in 2025.
- **`app/jobs/reindex.py`**: jobs only run if they're listed in `app/jobs/schedule.json`, and that file lists only `rollup-daily` and `prune-old`. Its docstring says search was replaced by a linear scan.
- **`app/util/old_format.py`**: `reindex.py` was the only thing that used it.

**Kept, though they look unused at first glance:** nothing imports these by name, but they're loaded at runtime from a string.
- **`app/exporters/xml_report.py`**: `load_exporter` builds the module name from the format, so `export xml` loads it this way.
- **`app/jobs/rollup_daily.py` and `app/jobs/prune_old.py`**: `run_all` loads them by the names in `schedule.json`. That's how `run-jobs` reaches them.
- **`app/util/dates.py` and `app/util/text.py`**: the store, the prune job and the stats summary use them.
- **The `.features/` folder, `FEATURES.md` and `AGENTS.md`**: these are the project's tooling for checking that features still work, not app code. None of them mentioned the deleted files, so I didn't edit them.

The repo isn't under git, so the deletions can't be undone with a checkout. You'd need another copy to get those files back.