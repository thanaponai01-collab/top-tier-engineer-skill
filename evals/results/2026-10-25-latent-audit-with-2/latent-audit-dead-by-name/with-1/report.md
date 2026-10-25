I removed 3 dead files from `fixture/` and kept everything else. Every command still works after the deletions: the feature map recheck reports 0 regressed, the unit tests pass, and `run-jobs`, `export xml` and `export json` give correct output.

## Removed
Each file was first deleted in a throwaway copy and checked with every app command: `run-jobs`, `export csv`, `export json`, `export xml`, `stats`, `list` and `add`. The feature map's recorded runs and the unit tests ran too. All three came back `nothing-breaks`.

| File | Why nothing reaches it |
|---|---|
| `app/legacy_sync.py` | Nothing imports or names it, and there's no config, schedule or cron entry for it. Its own docstring says the warehouse moved to CSV drops in 2025. |
| `app/jobs/reindex.py` | Jobs only run if they're listed by name in `app/jobs/schedule.json`, which has just `rollup-daily` and `prune-old`. `reindex` isn't there and isn't named anywhere else. |
| `app/util/old_format.py` | Only `reindex.py` used it. The first dead-code scan didn't flag it because `reindex.py` still pointed at it. I checked the two together as well: `nothing-breaks`. |

## Kept, though it looked dead
- **`app/jobs/rollup_daily.py`**: the scan said nothing referenced it, but the job runner loads it by name from `schedule.json` (`rollup-daily` becomes `rollup_daily`). Deleting it broke `python inv.py run-jobs` with `ModuleNotFoundError`, so it stays.
- **`app/exporters/xml_report.py`**: nothing imports it directly. `load_exporter` builds the module name from the format, so `inv.py export xml` reaches it.

## Watch
Nothing. All 4 suspects got a verdict and none were left unchecked.

## Not done
- **No commits:** `fixture/` isn't a git repository, so I couldn't make one commit per deletion as the audit process asks. The files are simply gone; if you want to be able to undo them, add the repo to git first.
- **Layer rules not checked:** the repo has no written layer order and I didn't make one up. If you give me one (e.g. `interface: inv.py` / `domain: app/jobs, app/report.py` / `data: app/store.py, app/util`), I can check the imports against it.

## Spotted along the way
`.features/export.json`'s recorded export run is `export csv`, but it records `xml_report.py` as the file covered, so the CSV path's own module isn't the one being tracked. `FEATURES.md` also says `export xml` was run, but only the CSV run is recorded. I didn't change either.