I mapped the notes CLI in `fixture/`, so the next session can read what it does instead of rediscovering it. Five of its six commands work. **`export` crashes on your real data.**

**What I added to `fixture/`:**
- **`FEATURES.md`**: one section per feature (Add, List, Search, Tag, Export, Purge). Each gives what it does for the user, the command, the path through the code (for example `add` @ notes.py > `run` @ commands/add.py > `save` @ store.py), what it changes, and how I know it works. `debug-dump` is listed under "Not features" because it's an undocumented command that just prints the raw notes file.
- **`AGENTS.md`**: tells the next agent to read `FEATURES.md` first and run `python .features/features.py check --rerun`. It also warns that `notes.json` holds your real notes, so anything that writes must be run on a copy.
- **`.features/`**: a copy of the checking script plus a saved record of each command's run. It works without the skill installed, so CI can use it too. Its check reports 0 problems on every count and exits 0. It will flag any later change that moves a command or stops one working.

**Your data:** `list` and `search` only read, so they ran in the repo. `add`, `tag`, `export` and `purge` ran in a throwaway copy of the repo. `notes.json` has the same hash as before I started, and I deleted the `__pycache__` folders my runs created. Running `check --rerun` later runs `list` and `search` again in the repo, which reads the notes but never changes them.

**Finding: `export` is broken.** `python notes.py export out.csv` exits with `ValueError: dict contains fields not in fieldnames: 'tags'`. In `commands/export.py`, the column list is only `id, title, body`, and Python's CSV writer stops with an error when a note has any other field. Every note has `tags`, so export fails every time. It's marked `failing` in the map, with the failed run saved. I didn't change the code. Either adding `"tags"` to the column list or telling the writer to ignore extra fields would fix it; once fixed, `prove --again` will move it to `proven`.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agents

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.

notes.json holds the owner's real notes: run anything that writes (add, tag, purge, export) with `prove --copy`, never in place.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the system has and how each feature is reached. The commands that keep it true need
no skill installed; their `--help` says the rest, so the script never needs reading:
- `python .features/features.py check --rerun`: every entry point against the code, and every
  recorded run (.features/<feature>.json) run again, naming what moved or stopped working.
- `python .features/features.py prove --feature "<name>" [--copy] -- <command>`: run an entry
  point and record it (`--copy` runs it in a throwaway copy, for anything that writes data).
- status: `proven` (a passing run is recorded), `failing` (a failing run is recorded), `traced`
  (read start to end, not run) or `suspected`, then how you know.

## Add
- what: Save a new note with a title, body and optional tags.
- cli: `add` @ notes.py
- trace: `add` @ notes.py > `run` @ commands/add.py > `save` @ store.py
- effect: appends a note (next id) to notes.json
- status: proven: `notes.py add Test hello --tag x` in a copy printed `added #4`

## List
- what: Show every note's id, title and tags, optionally only those with one tag.
- cli: `list` @ notes.py
- trace: `list` @ notes.py > `run` @ commands/listing.py > `all` @ store.py
- status: proven: `notes.py list --tag home` listed the home notes

## Search
- what: Find notes whose title or body contains a word (case-insensitive).
- cli: `search` @ notes.py
- trace: `search` @ notes.py > `run` @ commands/search.py > `all` @ store.py
- status: proven: `notes.py search dune` found #3 Books

## Tag
- what: Add a tag to an existing note by id.
- cli: `tag` @ notes.py
- trace: `tag` @ notes.py > `run` @ commands/tag.py > `save` @ store.py
- effect: rewrites notes.json with the tag added; exit 1 if the id does not exist
- status: proven: `notes.py tag 1 urgent` in a copy printed `tagged #1 urgent`

## Export
- what: Write all notes to a CSV file for a spreadsheet.
- cli: `export` @ notes.py
- trace: `export` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path
- status: failing: `notes.py export out.csv` crashes with `ValueError: dict contains fields not in fieldnames: 'tags'` (COLUMNS lacks `tags`, DictWriter raises on extra keys)

## Purge
- what: Delete every note, only when `--yes` is given.
- cli: `purge` @ notes.py
- trace: `purge` @ notes.py > `run` @ commands/purge.py > `save` @ store.py
- effect: empties notes.json and appends a line to purge.log beside it
- status: proven: `notes.py purge --yes` in a copy printed `all notes deleted` (never run on the real notes)

## Not features
- cli: `debug-dump` @ notes.py: developer dump of the raw notes.json, no help text, not a user command
