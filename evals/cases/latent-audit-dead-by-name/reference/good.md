Removed (nothing imports them, names them in a string or config, or schedules them; the map check
and every recorded run stay green without them):

- `app/legacy_sync.py`: pushes to the retired warehouse API; nothing references it.
- `app/jobs/reindex.py`: not in `schedule.json`, so `run_all` never loads it.
- `app/util/old_format.py`: only `reindex.py` used it, so it went dead with it.

Kept, though no import names them: `app/exporters/xml_report.py` is loaded by name through
`import_module(f"...{fmt}_report")` for `export xml`, and `app/jobs/rollup_daily.py` and
`app/jobs/prune_old.py` are loaded by name from `schedule.json` by `run_all`. Deleting either breaks
`run-jobs` or `export xml`; the unit tests would not notice.
