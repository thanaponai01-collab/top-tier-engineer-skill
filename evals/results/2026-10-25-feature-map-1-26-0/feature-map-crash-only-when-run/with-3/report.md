I've added a feature map, `fixture/FEATURES.md`, so the next agent session can start there instead of re-exploring the tool. It also found one real bug: **`export` crashes on your notes.**

**The map:** one section per command: `add`, `list`, `search`, `tag`, `export` and `purge`. Each section says what the command does, how to call it, and which code it goes through (`notes.py` → `commands/<x>.py` → `store.py` → `notes.json`). `debug-dump` is listed under "Not features": it has no help text and just prints the raw notes file. A note at the top warns that `notes.json` holds your real notes, so anything that writes to it should run in a copy.

**How I checked it:** I ran every command and kept the results in `.features/`, along with a copy of the checker (`.features/features.py`). That means the next session can confirm the map is still accurate without the skill installed: `python .features/features.py check --strict --rerun`. It exits 0 now, and it will fail if a command is renamed or removed, or if a command that worked stops working.

**Results:**
- `list`, `search`, `add`, `tag` and `purge --yes` all ran and exited 0, so they're marked proven. The four that write data (`add`, `tag`, `purge` and `export`) ran in a throwaway copy of the repo. `notes.json` is byte-identical to before, and I deleted the `__pycache__` folders my runs created.
- **`export` crashes:** `python notes.py export out.csv` fails with `ValueError: dict contains fields not in fieldnames: 'tags'`. In `commands/export.py`, the CSV writer only knows the columns `id`, `title` and `body`, but every note also has `tags`, so you never get a CSV. The map marks `export` as traced (code read, no working run) and describes the crash; the failed run is saved in `.features/export.json`. I didn't fix it because you asked for a map. The fix is to add `extrasaction="ignore"` to the `DictWriter`, or add a `tags` column; just say if you want it.

Nothing is committed, because `fixture/` isn't a git repository yet. `FEATURES.md` and `.features/` should be committed together.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the notes CLI can do and how each feature is reached. Every command is
`python notes.py <command> ...`; `notes.py` parses args and dispatches through `HANDLERS` to
`commands/<file>.py :: run(store, args)`. All data is `notes.json` (via `store.py`), which holds the
owner's real notes: run anything that writes (add, tag, export, purge) with `prove --copy` or in a copy.
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point
against the code and re-runs every recorded proof (.features/<feature>.json).

## Add
- what: Create a note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `notes.json` @ store.py
- effect: appends a note to notes.json (id = max id + 1); `--tag X` may repeat.
- status: proven: ran `add Test "a body" --tag x` in a copy, printed `added #4`

## List
- what: Show every note (id, title, tags), or only those with one tag via `--tag`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `notes.json` @ store.py
- status: proven: ran `list`, printed the 3 notes with tags

## Search
- what: Find notes whose title or body contains a text, case-insensitive.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `notes.json` @ store.py
- status: proven: ran `search dune`, printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (no-op if already tagged; exit 1 if no such note).
- cli: `tag` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `notes.json` @ store.py
- effect: rewrites notes.json with the tag added.
- status: proven: ran `tag 1 urgent` in a copy, printed `tagged #1 urgent`

## Export
- what: Write all notes to a CSV file (columns id, title, body) for a spreadsheet.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `COLUMNS` @ commands/export.py
- effect: creates/overwrites the CSV at the given path (relative to the current directory).
- status: traced: BROKEN — `export out.csv` crashes (ValueError: dict contains fields not in fieldnames: 'tags'); any note has `tags`, so it never writes rows. Receipt kept as failed in .features/export.json

## Purge
- what: Delete ALL notes; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `notes.json` @ store.py
- effect: empties notes.json and appends a line to purge.log beside it. Irreversible: never run on the real repo.
- status: proven: ran `purge --yes` in a copy, printed `all notes deleted`

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json, no help text, not a user command
