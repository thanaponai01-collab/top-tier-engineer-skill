I removed three files from `fixture/` and kept everything else. Afterwards `features.py check --rerun` came back clean (all 5 features rerun, 0 regressed), the unit tests passed (3/3), and `run-jobs` and `export xml` printed the right output.

## Removed
Before each deletion I deleted the file in a throwaway copy and re-ran everything that could load it: the map's recorded runs, the unit tests, `run-jobs`, `export csv`, `export json`, `export xml`, `stats` and `list`. None of them broke.

| File | Check result | Why nothing reaches it |
|---|---|---|
| `app/legacy_sync.py` | nothing breaks | No import, config, schedule or doc mentions it or its `push()`. Its own docstring says the warehouse API it posts to was replaced by CSV drops in 2025. |
| `app/jobs/reindex.py` | nothing breaks | Jobs are loaded only by the names in `app/jobs/schedule.json` (`rollup-daily`, `prune-old`). `reindex` isn't listed, and nothing else imports it. |
| `app/util/old_format.py` | nothing breaks (deleted together with `reindex.py`) | Its only importer was `reindex.py`. The audit tool didn't flag it, because that import made it look used. |

This folder isn't a git repo, so I couldn't make one commit per deletion. To undo one, you'd have to restore the file from a backup.

## Kept, though they looked dead
- **`app/jobs/rollup_daily.py`**: no import names it, but `run_all` loads it by building the name from `"rollup-daily"` in `schedule.json`. Deleting it made `inv.py run-jobs` fail with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: not in the `BUILT_IN` table. `load_exporter` loads it by building the name `f"{fmt}_report"`. Deleting it made `inv.py export xml` fail.
- **`app/jobs/prune_old.py`**: also loaded only by name (`prune-old` in the schedule). `FEATURES.md` lists it as part of Run Jobs.

## Watch
- No suspects are left unchecked: I checked all 4 the tool reported, plus `old_format.py`.
- **Outside callers I can't see**: `FEATURES.md` mentions a "nightly cron", but there's no crontab or deploy config in the repo. That cron runs `run-jobs` according to `schedule.json`, so it never reached `reindex`. If some other system imports `app.legacy_sync` directly, it now lives only in your backups.

## Layers
I didn't check layers, because the repo doesn't declare a layer order. That means unknown, not "clean". If you want them checked, write a layers file (top layer first) and I'll run it.

## Bugs noticed
- `.features/export.json`: `FEATURES.md` says Export was proven with `export xml` and `export csv`, but only the `csv` run is recorded. Running `features.py prove --again` would record the xml run so it gets rechecked too.