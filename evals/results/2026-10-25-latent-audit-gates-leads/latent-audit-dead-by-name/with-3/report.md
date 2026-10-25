I deleted three dead files and kept three that only looked dead. The audit's final check passes, and every command (`add`, `list`, `export csv/json/xml`, `stats`, `run-jobs`), the recorded feature runs and the unit tests behave the same as before.

**Removed.** I deleted each of these in a throwaway copy first, ran all of the above, and nothing broke:
- **`app/jobs/reindex.py`**: The job loader (`app/jobs/__init__.py:11`) imports jobs by name, but only the ones listed in `app/jobs/schedule.json`. That list is `["rollup-daily", "prune-old"]`. `reindex` isn't in it and nothing else mentions it, so it never runs.
- **`app/util/old_format.py`**: The only file that imported it was `reindex.py`, which never ran either.
- **`app/legacy_sync.py`**: Nothing imports it or calls its `push()` function. Its own comment says the warehouse API it talked to was replaced by CSV drops in 2025.

**Kept, though they looked dead.** Nothing imports these directly, but each one is loaded by name while the app runs:
- **`app/jobs/rollup_daily.py`**: It's listed as `"rollup-daily"` in `schedule.json`, so the job loader runs it. Deleting it made `python inv.py run-jobs` fail with `ModuleNotFoundError`.
- **`app/jobs/prune_old.py`**: It's listed as `"prune-old"` in `schedule.json`, and `FEATURES.md` names it under Run Jobs.
- **`app/exporters/xml_report.py`**: `load_exporter` builds the module name `xml_report` from the format you ask for, so it's what runs `inv.py export xml`. `FEATURES.md` names it under Export.

**Not done:**
- **Layer check:** The repo doesn't declare a layer order, so I couldn't check whether imports respect one. That is unknown, not a clean result.
- **Proof records:** The reasons and test results for each decision are in `fixture/.latent/verdicts.md`. The skill says to commit that folder with the deletions, but `fixture/` isn't a git repository, so nothing was committed.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: app/jobs/__init__.py:11 imports job modules by name, but only names listed in app/jobs/schedule.json:1 (["rollup-daily", "prune-old"]); "reindex" is not listed and nothing else spells it, so it never loads; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export json; run: python inv.py export csv; run: python inv.py stats; run: python inv.py list; run: python inv.py add spring 10
- app/jobs/rollup_daily.py: live: loaded dynamically by app/jobs/__init__.py:11 because app/jobs/schedule.json:1 lists "rollup-daily"; deleting it breaks map: recorded runs (features.py check --rerun)
- app/legacy_sync.py: dead: nothing imports or spells legacy_sync/push; its own docstring says the warehouse API was retired for CSV drops in 2025; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export json; run: python inv.py export csv; run: python inv.py stats; run: python inv.py list; run: python inv.py add spring 10
- app/util/old_format.py: dead: only importer is app/jobs/reindex.py:2 (itself dead, never loaded by app/jobs/__init__.py:11 since schedule.json omits it); deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export json; run: python inv.py export csv; run: python inv.py stats; run: python inv.py list; run: python inv.py add spring 10
