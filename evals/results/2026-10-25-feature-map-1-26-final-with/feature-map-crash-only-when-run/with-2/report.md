I added `fixture/FEATURES.md`, a feature map of the `notes` CLI. The next agent session can read it to see what the tool does instead of exploring the code again. I also added `fixture/.features/`, which holds a run record for each command and a copy of the checker. `python .features/features.py check --strict --rerun` exits 0, so every mapped command still exists in the code and every recorded run still gives the same result.

**What's in the map:** one section per command. Each says what the command does, the exact command line, and the call path from `notes.py` through `commands/*.py` to `store.py`/`notes.json`. It also says how I know it works.

| Feature | Status |
|---|---|
| `add`, `tag`, `purge` | Run and recorded working. These change notes, so I ran them only in a throwaway copy of the repo. |
| `list`, `search` | Run and recorded working. |
| `export` | **Broken.** It crashes, so it's labelled `traced` (code read end to end) rather than proven. |
| `debug-dump` | Listed under "Not features": it's a developer dump with no help text. |

**Bug found: `export` doesn't work.** `python notes.py export out.csv` exits 1 with `ValueError: dict contains fields not in fieldnames: 'tags'`. In `commands/export.py`, the CSV writer only expects `id, title, body`, but every note also has `tags`. One fix is to pass `extrasaction="ignore"` to `csv.DictWriter`. Another is to add `tags` as a column. I didn't change your code. The map records the failed run, so it will catch the change once you fix it.

**Your notes weren't touched.** `notes.json` is identical to the backup I took before starting. I then deleted that backup and the `__pycache__` folders the runs left behind.

`fixture/` isn't a git repo, so nothing is committed. If you put it under version control, commit `FEATURES.md` and `.features/` together. After any change that adds, renames or removes a command, a session should run `python .features/features.py check --rerun`.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

`notes`: a note-taking CLI, run as `python notes.py <command>`. Notes live in `notes.json` (the
owner's real notes: run anything that writes with `prove --copy`, never against this repo).
Keep it true: `python .features/features.py check --rerun` tests every entry point against the code
and re-runs every recorded proof (.features/<feature>.json), failing on any that broke.
Every command dispatches through `HANDLERS` in notes.py to `run(store, args)` in commands/.

## Add
- what: Save a new note with a title, body and optional tags (`--tag` repeatable); prints its id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json with id = max id + 1
- status: proven: `add` in a repo copy printed `added #4`, exit 0

## List
- what: Show every note's id, title and tags, or only notes with one tag (`--tag`).
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed notes #1 and #3, exit 0

## Search
- what: Find notes whose title or body contains a text, case-insensitive; prints id and title.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed `#3 Books`, exit 0

## Tag
- what: Add a tag to an existing note by id (no-op if already tagged; exit 1 if no such note).
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json
- status: proven: `tag 1 urgent` in a repo copy printed `tagged #1 urgent`, exit 0

## Export
- what: Write all notes to a CSV file (columns id, title, body) for a spreadsheet.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path
- status: traced: BROKEN, `export out.csv` exits 1 with `ValueError: dict contains fields not in fieldnames: 'tags'` (DictWriter has no extrasaction='ignore'); failed receipt in .features/export.json

## Purge
- what: Delete ALL notes; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`
- status: proven: `purge --yes` in a repo copy printed `all notes deleted`, exit 0

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json, no help text
