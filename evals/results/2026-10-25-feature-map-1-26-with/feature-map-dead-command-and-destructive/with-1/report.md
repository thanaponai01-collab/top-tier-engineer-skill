I've added a feature map at `fixture/FEATURES.md` so the next agent session can read what the `notes` CLI does instead of rediscovering it. The skill's checker (`features.py check --strict`) passes with no errors.

**What's in it:** five features, each with a one-line description, how to run it, and the code path from the command to `notes.json`:

| Feature | How I know it works |
|---|---|
| `add` | **Ran it** on a throwaway copy of the repo: it printed "added #4". Your real `notes.json` still has its 3 notes. |
| `list` | **Ran it** with `--tag home`. |
| `search` | **Ran it** with `dune`. |
| `export` | **Ran it**, writing to a temp file outside the repo. |
| `purge` | **Read the code only, didn't run it.** It deletes all notes, so it would need your go-ahead. |

The run records are kept in `fixture/.features/`. If any file a feature uses changes later, the checker flags that feature as out of date until it's run again.

**One bug found:** `python notes.py sync` shows up in `--help` as "sync notes with the cloud", but it has no code behind it in `notes.py`. Running it crashes with `TypeError: 'NoneType' object is not callable`. I listed it in the map as not a feature, and noted cloud sync as not built. I didn't change any code.

At the top of the map there's a warning that `notes.json` holds your real notes, with how to run `add` or `purge` on a copy instead. I also deleted the `__pycache__` folders my test runs created.

After any change that adds, renames or removes a command, run:
`python <feature-map skill>/scripts/features.py check --strict`

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached. Run everything from this directory as
`python notes.py <command>`. `notes.json` holds the owner's REAL notes: any command that writes
(add, purge) should be run against a copy (`cp -r . /tmp/notes-copy` and run that copy's
`notes.py`; `store.py` always uses the `notes.json` next to itself).
Check this map against the code with the `feature-map` skill: `features.py check --strict`.

## Add
- what: Save a new note with a title, a body and optional repeated `--tag`s; prints its new id.
- cli: `add` @ notes.py
- trace: `add` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: ran `add` against a copy of the repo, printed "added #4"

## List
- what: Print every note as `#id title  [tags]`, or only those carrying `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `list` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `list --tag home`, printed the two home notes

## Search
- what: Case-insensitive substring search over note titles and bodies; prints `#id title` per hit.
- cli: `search` @ notes.py
- trace: `search` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `search dune`, printed "#3 Books"

## Export
- what: Write all notes as indented JSON to the given file path.
- cli: `export` @ notes.py
- trace: `export` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at `path`; notes.json is only read
- status: proven: ran `export` to a temp file outside the repo

## Purge
- what: Delete ALL notes; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `purge` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`; destructive, not run
- status: traced: read notes.py HANDLERS > commands/purge.py > Store.save; not run (deletes data)

## Not features
- cli: `sync` @ notes.py: declared in the parser ("sync notes with the cloud") but has no entry in HANDLERS; running it crashes with TypeError 'NoneType' object is not callable

## Not built
Cloud sync: only the `sync` subcommand stub exists (see above). No edit or delete-one-note command.
