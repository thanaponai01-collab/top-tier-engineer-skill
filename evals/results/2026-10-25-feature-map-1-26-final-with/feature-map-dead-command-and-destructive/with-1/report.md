I added `fixture/FEATURES.md`, a map of what the CLI can do, and `fixture/.features/`, which holds a copy of the checker and the saved run results. A new session can read `FEATURES.md` and see every command, what it does and the code path behind it, without searching the code.

**What the map covers.** All five working commands (`add`, `list`, `search`, `export`, `purge`) are marked **proven**: I actually ran each one and kept the result. Each entry has a one-line description of what the command does, the path through the code from `notes.py` into `commands/*.py` and `store.py`, and, where it applies, what it changes on disk. The three commands that write data (`add`, `export`, `purge`) were run in a throwaway copy of the repo. Your real `notes.json` still has its 3 notes, and no `out.json` was left behind.

**Problem found: `sync` crashes.** The help text lists it as "sync notes with the cloud", but it was never connected to any code. `python notes.py sync` fails with `TypeError: 'NoneType' object is not callable`. I put it under "Not features" in the map with that reason, and noted under "Not built" that cloud sync doesn't exist. It's still checked, so the map will flag it once someone builds it.

**Check result.** `python .features/features.py check --strict --rerun` exits 0 with no problems in any category, and it re-ran all five commands successfully. Any session (or CI) can run that command to find out whether the map has gone out of date: renamed or removed commands, broken code paths, or commands that worked before and now fail. The `.features/` folder needs to be kept in the repo for that to work.

The folder isn't a git repository, so nothing was committed.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached (`python notes.py <command>`).
Notes are stored in `notes.json` (the owner's real notes: run anything that writes with `prove --copy`).
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof (.features/<feature>.json), failing on any that broke.

## Add
- what: Save a new note with a title, a body and optional repeatable `--tag`s; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: `notes.py add` run in a throwaway copy printed "added #4"

## List
- what: Print every note as `#id title [tags]`, optionally only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `notes.py list --tag home` printed the two home notes

## Search
- what: Print the notes whose title or body contains the query (case-insensitive).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `notes.py search dune` printed "#3 Books"

## Export
- what: Write all notes to a JSON file at the given path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at `<path>`
- status: proven: `notes.py export out.json` run in a throwaway copy printed "exported to out.json"

## Purge
- what: Delete every note; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]` — destroys the real notes; only ever prove with `--copy`
- status: proven: `notes.py purge --yes` run in a throwaway copy printed "all notes deleted"

## Not features
- cli: `sync` @ notes.py: declared in the argparse parser ("sync notes with the cloud") but has no entry in `HANDLERS`, so `notes.py sync` crashes with TypeError ('NoneType' object is not callable); nothing is synced

## Not built
Cloud sync (see `sync` above). No edit or delete-one-note command.
