I deleted three dead files from `fixture/`. Before deleting each one, I removed it in a throwaway copy and ran the app with it gone, and nothing broke. On the real tree afterwards, all 5 features (add, list, export, stats, run-jobs) still give their recorded output and the unit tests pass.

**Removed:**
- **`app/jobs/reindex.py`**: The job runner loads jobs by name (`app/jobs/__init__.py:11`), but only the names listed in `app/jobs/schedule.json`. That list is `rollup-daily` and `prune-old`, so `reindex` never runs.
- **`app/util/old_format.py`**: Its only user was `reindex.py`.
- **`app/legacy_sync.py`**: Nothing imports it or mentions it. Its own docstring says the warehouse API it pushed to was replaced by CSV drops in 2025.

**Kept, though they looked dead:**
- **`app/jobs/rollup_daily.py`**: Nothing imports it directly, but it's loaded by name from `schedule.json` (`"rollup-daily"`). Deleting it in the copy made `python inv.py run-jobs` fail with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: Loaded by name when you run `inv.py export xml` (`load_exporter` builds `{fmt}_report`). `FEATURES.md` lists it under Export.
- **`app/jobs/prune_old.py`**: Loaded by name from `schedule.json` (`"prune-old"`). `FEATURES.md` lists it under Run Jobs.
- **`app/util/dates.py`**: Still used by `store.py` and `prune_old.py`.

The repo doesn't define which code layers may import which, so I didn't check for layer violations at all. The audit records are in `.latent/verdicts.md`; commit that folder with the deletions so the next cleanup can start from them. `fixture/` isn't a git repository, so I haven't committed anything.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: app/jobs/__init__.py:11 builds job module names, but only from app/jobs/schedule.json:1, which lists rollup-daily and prune-old, never reindex, so it is never loaded; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list
- app/jobs/rollup_daily.py: live: loaded by name via app/jobs/schedule.json:1 ("rollup-daily") through app/jobs/__init__.py:11; deleting it breaks map: recorded runs (features.py check --rerun)
- app/legacy_sync.py: dead: no file imports or names it (warehouse moved to CSV drops per its docstring); deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list
- app/util/old_format.py: dead: its only importer was app/jobs/reindex.py:2, itself dead; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list
