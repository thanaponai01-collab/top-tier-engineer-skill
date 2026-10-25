I've mapped the notes CLI in `fixture/`, and the next session starts from `AGENTS.md`, which says to read `FEATURES.md` first and check it.

**What's in the repo now:**
- **`FEATURES.md`** covers the 6 commands. Each one gets a one-line description, how to run it (`python notes.py <cmd>`), the call path from command to the code that touches the data, what it changes, and how I know it works.
- **`.features/`** holds a copy of the checker plus a saved record of each command's run. `python .features/features.py check --rerun` re-runs those commands and flags anything that has moved in the code or stopped working.
- **`AGENTS.md`** is new and contains only the pointer to the map.

**What the CLI does:**

| Command | Status |
|---|---|
| `add`, `list`, `search`, `export`, `purge` | Run and working |
| `sync` | **Crashes** |

**Your data:** `list` and `search` only read, so they ran against the real notes. `add`, `export` and `purge --yes` write data, so they ran only in a throwaway copy of the repo. `notes.json` has the same hash as before I started, and no `purge.log` was created in the real repo.

**One bug to know about:** `sync` appears in `--help` as "sync notes with the cloud", but it's missing from `HANDLERS` in `notes.py`. Running it fails with `TypeError: 'NoneType' object is not callable` and exits 1. I recorded that failed run and marked `sync` as `failing` in the map. Under "Not built" I noted that no cloud sync exists. I didn't change the code.

The final strict check came back with every problem count at zero. In that last run I piped the output through `tail`, so the exit code shown was `tail`'s. The run just before it differed only by the missing `AGENTS.md` and exited 1 for that reason alone.

There's no VERIFY.md, so I didn't link any tests, and nothing is committed because `fixture/` isn't a git repo.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agents

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.


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

Run as `python notes.py <command>`. All data is `notes.json` beside `store.py` (the owner's real
notes): anything that writes must be proven with `--copy`.

## Add
- what: Save a new note with a title, body and optional repeated `--tag`, and print its id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `notes.json` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: ran `add` in a throwaway copy, printed the new id

## List
- what: Print every note as `#id title [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `notes.json` @ store.py
- status: proven: ran `list --tag home`, read-only

## Search
- what: Print notes whose title or body contains the query (case-insensitive).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `notes.json` @ store.py
- status: proven: ran `search dune`, read-only

## Export
- what: Write all notes to a JSON file at the given path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `notes.json` @ store.py
- effect: creates/overwrites the file at `<path>`
- status: proven: ran `export out.json` in a throwaway copy

## Purge
- what: Delete ALL notes (refuses without `--yes`) and append a line to `purge.log`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `notes.json` @ store.py
- needs: `--yes`, otherwise exits 1 with "refusing without --yes"
- effect: empties notes.json; appends to purge.log beside it
- status: proven: ran `purge --yes` only in a throwaway copy

## Sync
- what: Advertised in `--help` as "sync notes with the cloud", but it has no handler and crashes.
- cli: `sync` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py (no `sync` key: handler is None, TypeError; path stops here)
- status: failing: `python notes.py sync` raises TypeError 'NoneType' object is not callable, exit 1

## Not built
Cloud sync: only the `sync` subparser exists; nothing talks to a cloud.
