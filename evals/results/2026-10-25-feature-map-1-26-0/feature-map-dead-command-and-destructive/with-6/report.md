I mapped the notes CLI. The next agent session can read the map instead of exploring the code again, and `python .features/features.py check --strict --rerun` passes with exit 0.

**Files added to `fixture/`:**
- **`FEATURES.md`**: one section per command. Each says what the command does, its entry point in `notes.py`, the call path from the dispatcher through `commands/*.py` to `store.py`, what it changes, and its status.
- **`.features/`**: a stored record of each command's test run, plus a copy of the checker. The next session or CI can run `python .features/features.py check --rerun` to see what moved or broke since now, without the skill installed.
- **`AGENTS.md`**: tells the next agent to read `FEATURES.md` first. It also warns that `notes.json` holds your real notes, so anything that writes to it should run in a throwaway copy.

**Status of the six commands:**

| Command | Status | Where I ran it |
|---|---|---|
| `list`, `search` | proven (works) | in the repo (they only read) |
| `add`, `export`, `purge` | proven (works) | in a throwaway copy (they write data) |
| `sync` | **failing** | in the repo (it crashes before touching anything) |

**Your data:** `notes.json` is byte-for-byte unchanged before and after. No `purge.log` or export file was created in the repo, and I deleted the `__pycache__` folders the runs left behind.

**Bug found:** `sync` shows up in `--help` as "sync notes with the cloud", but it isn't implemented. `HANDLERS` in `notes.py` has no `sync` entry, so it crashes with `TypeError: 'NoneType' object is not callable`. It's recorded as a failing feature rather than left out of the map. I didn't change the code. The fix is either to write the command or to remove it from the parser.

**Also worth knowing:** `purge --yes` deletes every note with no undo. Without `--yes` it refuses and exits with code 1.

`fixture/` isn't a git repository, so nothing was committed. If you put it under version control, commit `.features/` together with `FEATURES.md`.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agents

Read FEATURES.md before driving or changing this app. `python .features/features.py check --rerun` says what moved or stopped working since it was proven.

`notes.json` holds the owner's real notes: run anything that writes (`add`, `export`, `purge`) only in a throwaway copy (`features.py prove --copy -- ...`).


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

All commands are `python notes.py <command>`; dispatch is `HANDLERS` in notes.py, and every
command reads/writes the real notes in `notes.json` via `store.Store` (store.py). Anything that
writes: run it with `prove --copy`, never against the repo's notes.json.

## Add
- what: Add a note with a title, a body and optional repeatable `--tag`s; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note (id = max id + 1) to notes.json
- status: proven: `add Test "a body" --tag x` in a copy printed `added #4`

## List
- what: Print every note as `#id title [tags]`, or only those with `--tag <tag>`.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed #1 Groceries and #3 Books

## Search
- what: Case-insensitive substring search over note titles and bodies; prints `#id title`.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed `#3 Books`

## Export
- what: Write all notes as indented JSON to the given file path.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at `<path>` (relative to cwd)
- status: proven: `export out.json` in a copy printed `exported to out.json`

## Purge
- what: Delete ALL notes; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: notes.json becomes `[]`; appends `purged all notes` to purge.log next to notes.json
- status: proven: `purge --yes` in a copy printed `all notes deleted` (destructive: only ever with --copy)

## Sync
- what: Advertised in `--help` as "sync notes with the cloud", but not implemented: it crashes.
- cli: `sync` @ notes.py
- trace: `HANDLERS` @ notes.py
- status: failing: `sync` exits 1 with TypeError 'NoneType' object is not callable; `HANDLERS` has no "sync" key, and no sync code exists anywhere
