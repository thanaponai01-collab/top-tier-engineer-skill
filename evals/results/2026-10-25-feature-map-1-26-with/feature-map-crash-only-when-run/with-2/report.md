I wrote `fixture/FEATURES.md`, a map of what the `notes` CLI can do. The proof that each command really ran is saved in `fixture/.features/`. `features.py check --strict` passes with every problem count at zero. A new agent session can read this one file and know every command, what it does, and how it moves through the code to `notes.json`.

**The export command is broken.** `commands/export.py` lists only `id, title, body` as columns, but every note also has `tags`, so the CSV writer raises a `ValueError` on the first note. When I ran `export`, it crashed with exit 1 and left a CSV with only the header row. I recorded the crash and marked Export `suspected` with the reason. I didn't fix it. There are two possible fixes: add `tags` as a column, or tell the writer to skip fields it doesn't know (`extrasaction="ignore"`). Tell me if you want one of them.

| Feature | Status | Evidence |
|---|---|---|
| list, search | proven | ran them in the repo (they only read) |
| add, tag | proven | ran them on a copy outside the repo |
| export | suspected | crashes, as described above |
| purge | traced | read the code, didn't run it |
| debug-dump | not a feature | developer dump with no help text |

**Your notes:** your README says `notes.json` holds your real notes. The path is hard-coded next to `store.py`, so I ran `add` and `tag` on a copy. `notes.json` has the same hash before and after.

**Purge** deletes everything and there's no backup, so I didn't run it. The map warns future agents about this too. There's no VERIFY.md in the repo, so I didn't link features to one.

**Keeping it current:** after any change that adds, renames or removes a command, run `features.py check` from the feature-map skill. It flags lines that have gone out of date and proofs taken before a file changed.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how to reach each feature. Run as `python notes.py <command>`.
All notes live in `notes.json` next to `store.py` (the path is fixed, not configurable). That file
holds the owner's real notes: run anything that writes (`add`, `tag`, `purge`) against a copy of
the repo, never here. `python features.py check` tests every line below against the code.

## Add
- what: Create a note with a title, a body and optional tags, and print its new id.
- cli: `add` @ notes.py
- trace: `add.run` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json (`id` = max id + 1)
- status: proven: ran `add` on a throwaway copy of the repo, printed `added #4`

## List
- what: Print every note as `#id title [tags]`, or only those carrying `--tag NAME`.
- cli: `list` @ notes.py
- trace: `listing.run` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `list --tag home`, printed notes #1 and #3

## Search
- what: Print the notes whose title or body contains a text, case-insensitive.
- cli: `search` @ notes.py
- trace: `search.run` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `search dune`, printed `#3 Books`

## Tag
- what: Add a tag to an existing note by id (no-op if already tagged; exit 1 if no such id).
- cli: `tag` @ notes.py
- trace: `tag.run` @ notes.py > `run` @ commands/tag.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json with the tag added
- status: proven: ran `tag 2 urgent` on a throwaway copy of the repo, printed `tagged #2 urgent`

## Export
- what: Write all notes to a CSV file (columns id, title, body) to open in a spreadsheet.
- cli: `export` @ notes.py
- trace: `export.run` @ notes.py > `run` @ commands/export.py > `DictWriter` @ commands/export.py
- effect: writes the CSV at the given path; reads notes.json only
- status: suspected: BROKEN IN CODE. `COLUMNS` lacks `tags`, so `DictWriter` raises ValueError on the first note; the run left a CSV with only the header row (failed receipt in .features/)

## Purge
- what: Delete every note; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `purge.run` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- needs: `--yes`
- effect: overwrites notes.json with `[]` (irreversible; there is no backup)
- status: traced: read the whole chain; not run because it deletes data

## Not features
- cli: `debug-dump` @ notes.py: developer dump of raw notes.json; no help text, same data as `list`
