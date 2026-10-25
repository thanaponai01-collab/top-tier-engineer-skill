I deleted three dead files from `fixture/`, and the CLI, the unit tests and all five features still pass. Before deleting anything, I ran every entry point and the tests and recorded which files they actually loaded. These three were never loaded, and no other file (config, schedule or docs) mentions them.

**Removed:**
- `app/legacy_sync.py`: sent stock to the old warehouse API, which its own comment says was retired in 2025. Nothing imports it.
- `app/jobs/reindex.py`: the job runner only loads jobs listed in `app/jobs/schedule.json`, and `reindex` isn't listed there.
- `app/util/old_format.py`: only `reindex.py` used it.

**Kept, though they looked dead (no file imports them by name):**
- `app/jobs/rollup_daily.py`: `schedule.json` lists it as `"rollup-daily"`, and the job runner loads it by that name. `inv.py run-jobs` prints its output.
- `app/jobs/prune_old.py`: also listed in `schedule.json` and loaded the same way.
- `app/exporters/xml_report.py`: `inv.py export xml` loads it by building its name from the format. Only csv and json are imported directly.

**Checks:** after the deletions, the audit helper's gate passes: 3 removed, 1 confirmed live, nothing left without a verdict. `features.py check --rerun` shows add, list, export, stats and run-jobs all exiting 0, as they did before. The reason for each removal is recorded in `.latent/verdicts.md`.

The repo didn't declare a layer order, so imports between layers weren't checked. The folder isn't a git repository, so nothing was committed. The skill expects `.latent/` to be committed with the change once you have version control.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: not listed in app/jobs/schedule.json, the only thing run_all loads from; no other file names it (deleted)
- app/legacy_sync.py: dead: nothing imports it or names it; the warehouse API it pushes to was retired in 2025 (deleted)
- app/util/old_format.py: dead: its only importer was app/jobs/reindex.py (deleted)
- app/jobs/rollup_daily.py: live: app/jobs/schedule.json:1 lists "rollup-daily", loaded by app/jobs/__init__.py:11
