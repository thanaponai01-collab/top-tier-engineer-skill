I added a feature map to `fixture/`, so the next session can start from it instead of exploring the code again.

**What's in the repo now**
- **`FEATURES.md`** (56 lines): one section per CLI command. Each says what the command does for the user, where the command is declared, the path from `notes.py` through the handler in `commands/` to `store.py`/`notes.json`, what it changes, and how I know it works.
- **`.features/`**: a recorded run for each command, plus a copy of the checker. `python .features/features.py check --rerun` compares the map against the code and reruns every recorded command, so it works without the skill installed.
- **`AGENTS.md`**: tells the next agent to read `FEATURES.md` first and run the check. It also warns that `notes.json` holds your real notes, so commands that write must run in a copy.

**The map**

| Command | What it does | Status |
|---|---|---|
| `list [--tag T]` | Prints notes, optionally filtered by tag | proven (ran here) |
| `search Q` | Case-insensitive search of titles and bodies | proven (ran here) |
| `add TITLE BODY [--tag T…]` | Adds a note and prints its new id | proven (ran in a throwaway copy) |
| `export PATH` | Writes all notes to a JSON file | proven (ran in a throwaway copy) |
| `purge --yes` | Deletes all notes and adds a line to `purge.log`; without `--yes` it refuses and exits 1 | proven (ran in a throwaway copy) |
| `sync` | Listed in `--help` as "sync notes with the cloud" | **failing** |

**Problem found:** `sync` doesn't work. It's declared in the argument parser but has no entry in `HANDLERS` (`notes.py:7`), so `main` calls `None` and crashes with `TypeError: 'NoneType' object is not callable`. No cloud-sync code exists anywhere, and the map says so under "Not built". I didn't change the code.

**Your data:** `add`, `export` and `purge` only ran in a throwaway copy of the repo. Your `notes.json` is unchanged and no `purge.log` was created.

`check --strict --rerun` passes with zero problems in every category. `fixture/` isn't a git repository, so nothing is committed. If you put it under git, commit `FEATURES.md`, `AGENTS.md` and `.features/` together.

<!-- file written by the agent: fixture/AGENTS.md -->
# AGENTS

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.

`notes.json` holds the owner's real notes: run anything that writes (add, export, purge) through `prove --copy` or in a copy, never against the repo.


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

All commands: `python notes.py <command>`; every one goes `main` > `HANDLERS` in notes.py >
`run` in commands/<file>.py > `Store` in store.py, which reads/writes `notes.json` (the owner's
real notes: run anything that writes with `prove --copy`).

## Add
- what: Save a new note with a title, body and optional repeatable `--tag`; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: ran in a throwaway copy, printed "added #4"

## List
- what: Print every note as `#id title [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed the two home notes

## Search
- what: Print notes whose title or body contains the query (case-insensitive substring).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed "#3 Books"

## Export
- what: Write all notes as a JSON array to the file path given.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the target file (path relative to the cwd)
- status: proven: ran in a throwaway copy, printed "exported to out.json"

## Purge
- what: Delete ALL notes; refuses (exit 1) without `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`, and a line is appended to purge.log beside it
- status: proven: ran `purge --yes` in a throwaway copy only, printed "all notes deleted"

## Sync
- what: Advertised in `--help` as "sync notes with the cloud", but has no handler: it crashes.
- cli: `sync` @ notes.py
- trace: `HANDLERS` @ notes.py > `main` @ notes.py
- status: failing: `HANDLERS` has no "sync" key, so `main` calls None and raises TypeError

## Not built
Cloud sync: only the argparse stub above exists; no code talks to any cloud.
