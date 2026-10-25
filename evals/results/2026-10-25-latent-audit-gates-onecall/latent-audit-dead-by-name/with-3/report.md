I deleted 3 dead files and kept 3 that looked dead but are used. The audit's final check passed, and afterwards everything still works on the real tree: all five commands (`add`, `list`, `export`, `stats`, `run-jobs`), the unit tests, and the recorded feature runs (`features.py check --rerun` reports 0 broken, 0 regressed).

Before deleting anything, I deleted each file in a throwaway copy and ran every CLI command against it. That included `run-jobs` and `export csv/json/xml`, because those load modules by building their names at runtime.

**Removed**
- **`app/legacy_sync.py`**: nothing imports it or mentions it. Its own description says the warehouse API it pushed to was retired in 2025.
- **`app/jobs/reindex.py`**: the job runner (`app/jobs/__init__.py:11`) only loads the jobs listed in `app/jobs/schedule.json`, which are `rollup-daily` and `prune-old`. `reindex` isn't listed, and nothing else mentions it.
- **`app/util/old_format.py`**: only `reindex.py` used it.

**Kept, though they looked dead**
- **`app/jobs/rollup_daily.py`**: no file imports it directly, but `schedule.json` lists `rollup-daily`, so the job runner loads it. Deleting it in the copy made `inv.py run-jobs` crash with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: nothing imports it directly, but `export xml` loads it by name through `load_exporter`.
- **`app/jobs/prune_old.py`**: loaded the same way as `rollup_daily.py`, because `schedule.json` lists `prune-old`.

The last two are also named in `FEATURES.md` as part of the Export and Run Jobs features.

**Gaps**
- I didn't check whether code in one layer imports from a layer above it, because the repo doesn't declare a layer order.
- The skill says to commit the `.latent/` folder (the record of these checks) with the change, so the next cleanup can start from it. `fixture/` isn't a git repository, so I couldn't commit; the folder is on disk at `fixture/.latent/`.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: app/jobs/__init__.py:11 imports only names listed in app/jobs/schedule.json:1 (`rollup-daily`, `prune-old`); `reindex` is not listed, and nothing else names it. Also deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
- app/jobs/rollup_daily.py: live: loaded by app/jobs/__init__.py:11 because app/jobs/schedule.json:1 lists `rollup-daily`; deleting it breaks `inv.py run-jobs` and map: recorded runs (features.py check --rerun)
- app/legacy_sync.py: dead: no import or name reference anywhere; its docstring says the warehouse API was retired in 2025; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
- app/util/old_format.py: dead: only importer is app/jobs/reindex.py:2 (itself dead); deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
