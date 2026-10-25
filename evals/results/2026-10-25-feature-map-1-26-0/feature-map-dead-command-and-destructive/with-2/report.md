I added a feature map to `fixture/`. The next session can read `FEATURES.md` instead of working out the CLI again. Its built-in check (`python .features/features.py check --strict --rerun`) passes: nothing is stale, broken, unmapped or unproven, and one entry is listed as not a feature (`sync`).

**What's in the repo now:**
- **`FEATURES.md`**: one section for each working command (`add`, `list`, `search`, `export`, `purge`). Each section says what the command does for the user, how to run it, and the code path it follows: `HANDLERS` in `notes.py` → `commands/<x>.py` `run` → `store.py`, which reads or writes `notes.json`. It also says what each command changes on disk and the run that proved it works.
- **`.features/`**: a saved record of each proving run, plus a copy of the checker script. The check runs without the feature-map skill installed. It reports when the code moves away from the map, and with `--rerun` it reruns the recorded commands to confirm they still work.
- **`README.md`**: I added one line at the end pointing to `FEATURES.md` and the check command.

**Things to know:**
- **`sync` is broken.** `notes.py` offers it ("sync notes with the cloud") but nothing handles it. `python notes.py sync` crashes with `TypeError: 'NoneType' object is not callable`. It didn't change any notes. I listed it as not a feature and noted that cloud sync isn't built. It isn't mapped as a working feature.
- **Your notes were not touched.** `add`, `export` and `purge` all write data, so I proved them in a throwaway copy of the repo. Afterwards I confirmed `notes.json` was byte-for-byte the same as before, and no `purge.log` was created.
- **Nothing is committed.** `fixture/` isn't a git repository. If you put it under git, commit `.features/` together with `FEATURES.md`.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What `notes` (a note-taking CLI, `python notes.py <command>`) can do and how each feature is reached.
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof (.features/<feature>.json), failing on any that broke.
Dispatch: `parser()` declares the subcommands, `HANDLERS` in notes.py maps each to `commands/<x>.run`,
which reads/writes `notes.json` through `store.Store`. notes.json holds the owner's real notes:
drive anything that writes with `prove --copy`.

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: `python notes.py add Test body --tag t` in a copy printed `added #4`

## List
- what: Show every note (id, title, tags), optionally only those with one tag.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `python notes.py list --tag home` printed #1 and #3

## Search
- what: Find notes whose title or body contains a text, case-insensitive.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `python notes.py search dune` printed #3 Books

## Export
- what: Write all notes to a JSON file at a path you give.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at the given path
- status: proven: `python notes.py export out.json` in a copy printed `exported to out.json`

## Purge
- what: Delete all notes, only with `--yes`; leaves a line in purge.log beside notes.json.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; appends to purge.log. Without `--yes` it refuses and exits 1.
- status: proven: `python notes.py purge --yes` in a copy printed `all notes deleted`

## Not features
- cli: `sync` @ notes.py: declared in `parser()` ("sync notes with the cloud") but has no entry in `HANDLERS`; `python notes.py sync` crashes with `TypeError: 'NoneType' object is not callable`, exit 1, notes unchanged

## Not built
Cloud sync: only the `sync` subcommand stub exists (see above); there is no sync code.
