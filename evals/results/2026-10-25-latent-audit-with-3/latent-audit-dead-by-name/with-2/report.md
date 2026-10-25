I deleted 3 dead files. All five commands (`add`, `list`, `export` in csv/json/xml, `stats`, `run-jobs`) and the unit tests pass afterwards, and `features.py check --rerun` reports nothing broken.

## Removed
Before each deletion, the helper deleted the file in a throwaway copy and ran every command plus the tests before and after. Each got the verdict `nothing-breaks`.

| File | Why nothing reaches it |
|---|---|
| `app/jobs/reindex.py` | Jobs are only loaded by the names in `app/jobs/schedule.json`, and that list is just `rollup-daily` and `prune-old`. Its docstring says it was replaced when search moved to a linear scan. |
| `app/util/old_format.py` | Its only importer was `reindex.py`, so it was removed in the same check. The graph tool didn't flag it, because `reindex.py` still imported it. |
| `app/legacy_sync.py` | Nothing imports it or mentions it anywhere, by any spelling. Its own docstring says the warehouse moved to CSV drops in 2025. There's no cron entry, config or other caller pointing to it. |

The folder isn't a git repo, so I couldn't commit each deletion separately as the skill asks. To undo, you'd have to restore the files from elsewhere.

## Kept, though they looked dead
No import names these files, but both are loaded by name at runtime:
- **`app/jobs/rollup_daily.py`**: `run_all` loads it because `schedule.json` lists `"rollup-daily"`. Deleting it in the copy made `inv.py run-jobs` fail with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: `load_exporter` builds the name `f"{fmt}_report"` for `export xml`. Deleting it made `inv.py export xml` fail.
- **`app/jobs/prune_old.py`**: also loaded by name from `schedule.json`. FEATURES.md lists it as part of Run Jobs.

## Watch
Nothing. All 5 suspects were checked.

## Layers
Not checked. The repo has no written layer order, and I didn't make one up.

## Noted along the way
- `.features/export.json:7`: the only saved run for Export is `export csv`, but `FEATURES.md:29` says both `xml` and `csv` were run. The XML path, which is the one loaded dynamically, has no saved run that would catch a break; I only found it by passing `export xml` explicitly. Running `python .features/features.py prove --feature "Export" -- python inv.py export xml` would record one.