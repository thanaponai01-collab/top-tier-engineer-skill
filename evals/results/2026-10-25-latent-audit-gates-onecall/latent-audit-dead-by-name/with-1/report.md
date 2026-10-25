I deleted three dead files. Everything still works: the unit tests pass, all five features (add, list, export, stats, run-jobs) re-run with the same results as when they were first recorded, and the audit's final check reports done.

**Removed.** Before each deletion, I deleted the file in a throwaway copy of the repo and ran the tests plus every CLI command (`add`, `list`, `export csv/json/xml`, `stats`, `run-jobs`). Nothing broke.
- `app/jobs/reindex.py`: jobs are loaded by name at `app/jobs/__init__.py:11`, but only the names listed in `app/jobs/schedule.json` (`rollup-daily`, `prune-old`). `reindex` isn't on that list, so it never loads. Its docstring says search moved to a linear scan.
- `app/util/old_format.py`: only `reindex.py` used it.
- `app/legacy_sync.py`: nothing imports it, and its docstring says the old warehouse API it pushes to was replaced by CSV drops in 2025. Nothing in the repo calls it. A script outside the repo that imports it would be the only thing that could break, and I can't check for that from here.

**Kept, though it looked dead.** Nothing imports these directly:
- `app/jobs/rollup_daily.py`: loaded by name from `schedule.json` (`"rollup-daily"`). Deleting it in the copy made `inv.py run-jobs` fail with `ModuleNotFoundError`.
- `app/jobs/prune_old.py`: also listed in `schedule.json` and run by `run-jobs`. `FEATURES.md` lists it under the Run Jobs feature.
- `app/exporters/xml_report.py`: loaded by name for `inv.py export xml` (`app/exporters/__init__.py` builds `{fmt}_report`). `FEATURES.md` lists it under Export.

**Not covered:**
- I didn't check that imports respect any layer order, because the repo doesn't define one.
- `fixture/` isn't a git repo, so nothing is committed. The skill recommends committing `.latent/verdicts.md` along with the deletions, since it records the reasoning for each file and the next cleanup can start from it.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: app/jobs/__init__.py:11 imports only names listed in app/jobs/schedule.json:1 ("rollup-daily", "prune-old"), which never builds "reindex"; its docstring says search moved to a linear scan; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
- app/jobs/rollup_daily.py: live: loaded by name via app/jobs/__init__.py:11 from app/jobs/schedule.json:1 ("rollup-daily"); deleting it breaks map: recorded runs (features.py check --rerun)
- app/legacy_sync.py: dead: deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
- app/util/old_format.py: dead: deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export csv; run: python inv.py export json; run: python inv.py export xml; run: python inv.py stats; run: python inv.py list; run: python inv.py add widget 3
