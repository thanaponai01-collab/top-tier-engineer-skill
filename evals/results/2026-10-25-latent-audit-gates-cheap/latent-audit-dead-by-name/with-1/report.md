I deleted three files from `fixture/`. Before each deletion, the skill's helper deleted the file in a throwaway copy and confirmed nothing broke: the recorded feature runs, the unit tests, and the `run-jobs`, `export xml`/`json`, `stats` and `list` commands. After the real deletions I ran `run-jobs`, `export xml` and the unit tests again, and all pass. The audit's final check reports `LATENT-GATE: done`.

**Removed:**
- **`app/jobs/reindex.py`**: Jobs are loaded by name: `app/jobs/__init__.py:11` imports whatever `app/jobs/schedule.json` lists. That list is only `rollup-daily` and `prune-old`, so nothing ever loads `reindex`.
- **`app/legacy_sync.py`**: Nothing imports or mentions it, and its `push()` is never called. Its own docstring says the warehouse API it calls was replaced by CSV drops in 2025.
- **`app/util/old_format.py`**: Its only user was `reindex.py`, so it became dead along with it.

**Kept, though it looked dead:**
- **`app/jobs/rollup_daily.py`**: No code imports it, but `schedule.json` names `rollup-daily` and the job loader imports it by that name. Deleting it in the copy made `python inv.py run-jobs` fail with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: `load_exporter` builds `xml_report` from the format name, and `export xml` is a documented feature in `FEATURES.md`.
- **`app/jobs/prune_old.py`**: It's loaded by name from `schedule.json` in the same way, and the Run Jobs feature in `FEATURES.md` depends on it.

**Notes:**
- The audit's reasons for each decision are recorded in `fixture/.latent/verdicts.md`. `fixture/` isn't a git repository, so nothing was committed. If you put it under git, commit `.latent/` along with the deletions so the next cleanup can start from that record.
- I didn't check for imports that break the app's layering, because the repo doesn't declare a layer order. That means it wasn't checked, not that it's clean.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: the only loader in its package, app/jobs/__init__.py:11, imports names from app/jobs/schedule.json:1, which lists only rollup-daily and prune-old, so it never loads reindex; try-delete broke none of the recorded runs, unit tests, or run-jobs/export/stats/list runs
- app/jobs/rollup_daily.py: live: app/jobs/schedule.json:1 names "rollup-daily", loaded by app/jobs/__init__.py:11; deleting it breaks `python inv.py run-jobs` (ModuleNotFoundError)
- app/legacy_sync.py: dead: no import or textual reference anywhere (push() is unused; the warehouse moved to CSV drops); try-delete broke none of the recorded runs, unit tests, or CLI runs
- app/util/old_format.py: dead: its only importer was app/jobs/reindex.py (itself dead); try-delete broke none of the recorded runs, unit tests, or CLI runs
