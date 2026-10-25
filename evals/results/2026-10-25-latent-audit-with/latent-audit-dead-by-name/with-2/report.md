I deleted three files. Every command that could load them still works afterwards: all four features re-ran with the same exit codes as their recorded runs, the unit tests pass, and `run-jobs` still prints both jobs.

## Removed
Each file passed a delete check in a throwaway copy first. The check ran `run-jobs`, `export csv/json/xml`, `stats`, `list`, the recorded feature runs and the unit tests. All of them still passed, so the result was `nothing-breaks`. I also tested deleting all three together, and nothing broke.

| File | Why nothing reaches it |
|---|---|
| `app/jobs/reindex.py` | Jobs are only loaded by name from `app/jobs/schedule.json`, which lists `rollup-daily` and `prune-old` but not `reindex`. Its docstring says it was replaced. |
| `app/util/old_format.py` | Its only importer was `reindex.py`. The audit tool didn't flag it because that importer existed, so I traced it by hand. |
| `app/legacy_sync.py` | No imports, no loader and no config reference it. Its own docstring says the warehouse moved to CSV drops in 2025. |

The fixture isn't a git repo, so I couldn't make one commit per deletion as the skill asks. Each deletion was just removing a file, with no tests or config pointing at it, so there was nothing else to clean up.

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: nothing imports it directly, but `run_all` loads it through `import_module` because `schedule.json` lists `rollup-daily`. Deleting it in the copy broke `python inv.py run-jobs` with `ModuleNotFoundError`.
- **`app/exporters/xml_report.py`**: also loaded by a built name (`import_module(f"...{fmt}_report")`) when you run `inv.py export xml`. It's listed in FEATURES.md as part of Export, so it was never a suspect.

## Watch
- None. All 4 suspects were checked; none are left.
- **Layers were not checked**: the repo has no written layer order, so this is a gap, not a clean result.
- `legacy_sync.push` made calls to an external API. If some script outside this repo imported it, I couldn't see that from here. Nothing in the repo or its docs points to such a caller.

## Bugs noticed (not fixed)
- `app/exporters/csv_report.py:6`: the CSV writer fails if an item has any field other than `id/name/qty/added`. It works on today's data.