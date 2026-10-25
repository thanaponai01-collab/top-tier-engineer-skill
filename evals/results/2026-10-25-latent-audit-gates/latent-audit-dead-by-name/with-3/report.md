I deleted three dead files. Everything that's used still works, including the files that looked dead but aren't. Each file was deleted in a throwaway copy first. Every CLI command (`add`, `list`, `export csv/json/xml`, `stats`, `run-jobs`), the recorded feature runs and the unit tests passed before and after, and only then did I remove it for real. The skill's final check, `LATENT-GATE: done`, passes.

**Removed:**
- `app/jobs/reindex.py`: it isn't listed in `app/jobs/schedule.json:1` and nothing imports it. Its own docstring says it was replaced.
- `app/util/old_format.py`: the only thing that imported it was `reindex.py`.
- `app/legacy_sync.py`: nothing in the repo refers to it, and its docstring says the warehouse API it pushed to was retired in 2025.

**Kept, though it looked dead:**
- `app/jobs/rollup_daily.py`: no code imports it directly. `app/jobs/schedule.json:1` lists it by name and `app/jobs/__init__.py:11` loads it at runtime. Deleting it in the copy broke `inv.py run-jobs` with `ModuleNotFoundError`.
- `app/exporters/xml_report.py`: `load_exporter` in `app/exporters/__init__.py` loads it by name for `inv.py export xml`. `FEATURES.md` names it, and that run passes.
- `app/jobs/prune_old.py`: loaded by name through `schedule.json`, same as `rollup_daily`. `FEATURES.md` names it.

**Things to know:**
- I only checked whether each file was used, not whether imports respect a layer order. No layer order is declared, so that's unchecked, not confirmed clean.
- The audit only sees callers inside this repo. If something outside it imports `app.legacy_sync` directly, that caller would break. Nothing suggests one exists.
- The proof is saved in `.latent/verdicts.md`. The folder isn't a git repo, so nothing is committed. Keep `.latent/` with the change so the next cleanup can start from it.
- Your real `items.json` wasn't touched. The `add` test ran in the copy.

<!-- file written by the agent: fixture/.latent/verdicts.md -->
# Verdicts

One line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the
`file:line` that reaches it.

- app/jobs/reindex.py: dead: not listed in app/jobs/schedule.json:1, nothing imports it; try-delete with every CLI command and the map runs passed
- app/jobs/rollup_daily.py: live: loaded by name from app/jobs/schedule.json:1 via import_module in app/jobs/__init__.py:11; try-delete broke `inv.py run-jobs`
- app/legacy_sync.py: dead: no reference anywhere in-tree, its own docstring says the warehouse API was retired in 2025; try-delete with every CLI command passed
- app/util/old_format.py: dead: only importer was app/jobs/reindex.py (dead); try-delete with every CLI command passed
