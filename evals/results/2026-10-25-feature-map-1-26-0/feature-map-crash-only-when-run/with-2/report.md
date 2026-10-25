I added `fixture/FEATURES.md` and `fixture/.features/`, so the next session can read what the tool does instead of working it out again. `check --strict --rerun` comes back clean: 0 stale, 0 broken, 0 unmapped, 0 unproven, 0 regressed. One command, `export`, is broken.

**What the map covers:** six features (`add`, `list`, `search`, `tag`, `export`, `purge`). Each one has a one-line description, the exact command to type, and the path through the code from the command to the file it changes. `debug-dump` is listed under "Not features" as a developer command with no help text.

**How I tested them:** I ran every command and kept the exit code and output as a receipt in `.features/<feature>.json`. The commands that write data (`add`, `tag`, `purge --yes`, `export`) ran in a throwaway copy of the folder. Your real `notes.json` has the same checksum before and after, and no `purge.log` was created.

**The broken command:** `python notes.py export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'`. Every note has a `tags` key, but the CSV columns in `commands/export.py` are only `id, title, body`, so the output file ends up with just the header row. The map marks it as broken with the error, and its failed run is saved. I didn't fix it. The fix is either `DictWriter(..., extrasaction="ignore")` or adding a `tags` column. Tell me if you want me to make that change.

**For the next session:** read `FEATURES.md` first. Then run `python .features/features.py check --strict --rerun`, which reruns the saved commands. It reports any command that was renamed or stopped working since the map was written, and it doesn't need the skill installed. Also run it after any change to the commands.

The folder isn't a git repository, so nothing is committed. Commit `.features/` together with `FEATURES.md` if you put it under version control.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how to reach each feature. Run everything as `python notes.py <command>`
from this directory. All data is in `notes.json` (the owner's real notes): run anything that writes
with `prove --copy` or on a copy, never on the real file.
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof in `.features/<feature>.json`.

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- usage: `python notes.py add "<title>" "<body>" [--tag T ...]`
- trace: `add.run` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json (id = max id + 1)
- status: proven: ran in a throwaway copy, printed `added #4`

## List
- what: Show every note as `#id title [tags]`, optionally only those with one tag.
- cli: `list` @ notes.py
- usage: `python notes.py list [--tag T]`
- trace: `listing.run` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed notes #1 and #3

## Search
- what: Find notes whose title or body contains a word (case-insensitive).
- cli: `search` @ notes.py
- usage: `python notes.py search <query>`
- trace: `search.run` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (no duplicate tags); exits 1 if the id does not exist.
- cli: `tag` @ notes.py
- usage: `python notes.py tag <id> <name>`
- trace: `tag.run` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag added
- status: proven: ran in a throwaway copy, printed `tagged #1 urgent`

## Export
- what: Write all notes to a CSV (columns id, title, body) to open in a spreadsheet.
- cli: `export` @ notes.py
- usage: `python notes.py export <out.csv>`
- trace: `export.run` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV file at the given path
- status: traced: BROKEN in practice. Running it crashes with `ValueError: dict contains fields not in fieldnames: 'tags'` (notes have a `tags` key that `COLUMNS` lacks); the output file is left with only the header. Failed receipt in .features/export.json.

## Purge
- what: Delete ALL notes (needs `--yes`, otherwise refuses and exits 1) and append a line to purge.log.
- cli: `purge` @ notes.py
- usage: `python notes.py purge --yes`  (destructive: empties notes.json; never run on the real repo)
- trace: `purge.run` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; `purge.log` created/appended next to it
- status: proven: ran `purge --yes` in a throwaway copy, printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer command (no help text), prints the raw notes.json as JSON
