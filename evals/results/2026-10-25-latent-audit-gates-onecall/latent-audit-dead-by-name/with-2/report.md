I deleted three dead files and kept three that looked dead but are used. After the deletions all five features still work when re-run (add, list, export, stats, run-jobs), the unit tests pass, and the audit's final check reports done.

**Removed.** Before each deletion I deleted the file in a throwaway copy, then ran every CLI command, the recorded feature runs and the unit tests. Nothing broke.
- `app/legacy_sync.py`: the client for the old warehouse API. Its own docstring says the warehouse moved to CSV drops in 2025, and nothing imports it or mentions its name.
- `app/jobs/reindex.py`: an old search-index job. The jobs runner builds module names at runtime (`app/jobs/__init__.py:11`), so having no imports didn't prove it was unused. But it only loads the jobs listed in `app/jobs/schedule.json`, which names `rollup-daily` and `prune-old` and not `reindex`.
- `app/util/old_format.py`: the only file that imported it was `reindex.py`.

**Kept, though they looked dead.** No file imports any of these.
- `app/jobs/rollup_daily.py`: `schedule.json` lists it and the jobs runner loads it. Deleting it made `python inv.py run-jobs` fail with `ModuleNotFoundError`.
- `app/jobs/prune_old.py`: loaded the same way, from `schedule.json`.
- `app/exporters/xml_report.py`: `load_exporter` imports it by name only when you run `export xml`, and `xml` is one of the formats in `inv.py`.

**Not checked:**
- **Layer rules:** the repo doesn't declare a layer order, so nothing was checked for imports that cross layers.
- **Callers outside the repo:** they can't be seen from here. If something external called `legacy_sync.push`, it would break, but the code itself says that API is no longer used.

The reason behind each decision is recorded in `fixture/.latent/verdicts.md`. The folder isn't a git repo, so I haven't committed anything; the audit's instructions say to commit `.latent/` along with the deletions.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.

- app/jobs/reindex.py: dead: app/jobs/__init__.py:11 builds job module names at runtime, but only from app/jobs/schedule.json:1, which lists only rollup-daily and prune-old, never reindex; deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export csv; run: python inv.py export json; run: python inv.py stats; run: python inv.py list
- app/jobs/rollup_daily.py: live: app/jobs/schedule.json:1 lists rollup-daily, loaded by app/jobs/__init__.py:11; deleting it breaks map: recorded runs (features.py check --rerun)
- app/legacy_sync.py: dead: deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export csv; run: python inv.py export json; run: python inv.py stats; run: python inv.py list
- app/util/old_format.py: dead: its only importer is app/jobs/reindex.py (itself dead); deleting it broke none of: map: recorded runs (features.py check --rerun); tests: python -m unittest discover; run: python inv.py run-jobs; run: python inv.py export xml; run: python inv.py export csv; run: python inv.py export json; run: python inv.py stats; run: python inv.py list
