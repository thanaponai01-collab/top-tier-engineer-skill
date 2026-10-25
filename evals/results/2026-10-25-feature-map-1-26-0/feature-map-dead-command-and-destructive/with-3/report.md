I mapped the `notes` CLI into `fixture/FEATURES.md`, so the next agent session can read what the tool does instead of working it out again. I also found one bug: the `sync` command is listed in `--help` but crashes when you run it.

**What I left in the repo:**
- **`FEATURES.md`** has one section per feature: what it does, how to run it, the path through the code to the data it changes, and how I confirmed it works.
- **`.features/`** holds a saved record of each command's test run, plus a copy of the checker script. It works even where the feature-map skill isn't installed.
- **`README.md`** has one new line pointing to the map and the command that checks it.

**The five working commands:**

| Command | What it does | Changes data |
|---|---|---|
| `add` | Saves a note with a title, body and optional tags | `notes.json` |
| `list` | Lists all notes, or only those with a given tag | — |
| `search` | Finds notes whose title or body contains a word (ignores case) | — |
| `export` | Writes all notes to a JSON file you name | the file you name |
| `purge --yes` | Deletes every note; refuses without `--yes` | `notes.json`, and adds a line to `purge.log` |

I ran all five and each exited cleanly. The three that write data (`add`, `export`, `purge`) ran in a throwaway copy of the repo. Your `notes.json` still holds notes 1–3, and no `purge.log` or export file was created. The final map check passed with no problems.

**The `sync` bug:** the command is defined, but there's no code behind it, so it fails with `TypeError: 'NoneType' object is not callable`. I listed it in the map as a known non-working command and noted that cloud sync isn't built. I didn't add a guard or remove it from `--help`, because that's your call.

**For the next session:** run `python .features/features.py check --rerun` first. It reruns the saved tests and points out anything that has moved or stopped working since the map was written. Run it again after adding, renaming or removing a command. `fixture/` isn't a git repository, so none of this is committed.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached (`python notes.py <command>`).
Notes live in `notes.json` (the owner's real notes: run anything that writes with `prove --copy`).
Keep it true: `python .features/features.py check --strict --rerun` tests every entry point against
the code and re-runs every recorded proof (.features/<feature>.json), failing on any that broke.

## Add
- what: Save a new note with a title, a body and optional repeated `--tag`s; prints its new id.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: ran `notes.py add` in a throwaway copy, printed `added #4`

## List
- what: Print every note as `#id title [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `notes.py list --tag home`, printed the two home notes

## Search
- what: Print notes whose title or body contains the query (case-insensitive).
- cli: `search` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `notes.py search dune`, printed `#3 Books`

## Export
- what: Write all notes as indented JSON to the file path given.
- cli: `export` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at `<path>`
- status: proven: ran `notes.py export out.json` in a throwaway copy, printed `exported to out.json`

## Purge
- what: Delete ALL notes; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; appends `purged all notes` to purge.log beside it
- status: proven: ran `notes.py purge --yes` in a throwaway copy, printed `all notes deleted`

## Not features
- cli: `sync` @ notes.py: declared in the parser and shown in `--help`, but HANDLERS has no `sync` entry, so it crashes with `TypeError: 'NoneType' object is not callable` (exit 1)

## Not built
Cloud sync: only the `sync` subparser exists; there is no handler and no sync code.
