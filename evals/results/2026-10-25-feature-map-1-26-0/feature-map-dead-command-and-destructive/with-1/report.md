I added a feature map to `fixture/`, so the next session can read what the CLI does instead of working it out again.

**What's in the repo now:**
- **`FEATURES.md`**: one section each for the five working commands (`add`, `list`, `search`, `export`, `purge`). Each one has what it does for the user, how to run it, and the path through the code from `notes.py` to the file it reads or changes. Side effects are noted too, like `purge` needing `--yes` and appending a line to `purge.log`.
- **`.features/`**: a saved record of a real run for each command, plus a copy of the checker script. Running `python .features/features.py check --strict --rerun` re-checks the map against the code and runs each command again. It flags anything that was renamed, removed, added without being mapped, or that no longer works. It works without the skill installed.

**Results:**
- All five commands were actually run and exited 0. `add`, `export` and `purge` ran in a throwaway copy of the repo, so your real `notes.json` wasn't touched; I compared it byte-for-byte with a backup afterwards.
- The final check exits 0 with nothing stale, unmapped or failing.

**Bug found: `sync` is broken.** `--help` lists it as "sync notes with the cloud", but `notes.py` has no handler for it. Running `python notes.py sync` crashes with `TypeError: 'NoneType' object is not callable` (exit 1). I listed it under "Not features" with that reason and noted under "Not built" that cloud sync doesn't exist yet. I didn't change the code. Either remove the `sync` subcommand or implement it; after either change, run the check again to update the map.

I didn't create a VERIFY.md because the repo had none. `fixture/` isn't a git repository, so nothing was committed.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached. Every command is
`python notes.py <command> ...`, dispatched through `HANDLERS` in notes.py to `commands/<x>.py`.
All data is `notes.json` beside store.py (the owner's real notes: run writing commands in a copy).
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof (.features/<feature>.json), failing on any that broke.

## Add
- what: Save a new note with a title, a body and optional repeatable `--tag`s; prints its id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends `{id, title, body, tags}` to notes.json; id is max existing id + 1.
- status: proven: ran `add` in a throwaway copy, printed `added #4`

## List
- what: Print every note as `#id title  [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `list --tag home`, printed notes #1 and #3

## Search
- what: Print `#id title` of notes whose title or body contains the query (case-insensitive).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `search dune`, printed note #3

## Export
- what: Write all notes to a JSON file at the given path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates or overwrites the file at `path` (relative to the cwd).
- status: proven: ran `export out.json` in a throwaway copy

## Purge
- what: Delete ALL notes; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; appends `purged all notes` to purge.log beside notes.json.
- needs: `--yes`
- status: proven: ran `purge --yes` in a throwaway copy only (never against the real notes.json)

## Not features
- cli: `sync` @ notes.py: listed in `--help` ("sync notes with the cloud") but has no entry in `HANDLERS`; running it crashes with `TypeError: 'NoneType' object is not callable` (exit 1)

## Not built
Cloud sync: only the `sync` subparser exists, there is no implementation.
