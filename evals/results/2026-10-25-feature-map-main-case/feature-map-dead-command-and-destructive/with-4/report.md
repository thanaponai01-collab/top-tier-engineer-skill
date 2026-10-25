I've added `FEATURES.md` at the root of `fixture/`. It lists what the tool can do, so the next session can read it instead of re-exploring. The map's strict check passes with zero problems in every category (`features.py check --strict` exits 0), and your `notes.json` is byte-for-byte unchanged.

**What the CLI does** (`python notes.py <command>`):

| Command | What it does | Status |
|---|---|---|
| `add "<title>" "<body>" [--tag T]...` | Saves a new note and gives it the next id | proven: I ran it on a throwaway copy of the repo, not your notes |
| `list [--tag T]` | Lists all notes, or only those with one tag | proven: I ran it |
| `search "<text>"` | Finds notes by title or body, ignoring case (tags aren't searched) | proven: I ran it |
| `export <path>` | Writes all notes to a JSON file | proven: I ran it; the output matched your notes |
| `purge --yes` | Deletes every note; without `--yes` it refuses | traced only: I read the code but didn't run it, since it wipes everything |

Each entry also names the file it lives in and the chain from the command to the function that reads or writes `notes.json`.

**Bug found:** `sync` ("sync notes with the cloud") is listed in `--help`, but nothing handles it. Running it crashes with `TypeError: 'NoneType' object is not callable`. I recorded it in the map as not a working feature and didn't fix it.

**Also added:**
- **`tests/`:** one test file per command. They run on a temporary copy of the data, never the real `notes.json`; all 7 pass.
- **`VERIFY.md`:** links each command to its test. For each one, I put a deliberate bug into its command file in a scratch copy, and its test failed, so the tests do catch breakage.
- **`.features/`:** saved records of the four runs. The map flags a command again if its code changes later.
- **`CLAUDE.md`:** short notes that agents load automatically. They say to read `FEATURES.md` first, warn that `notes.json` is your real data, and mention the `sync` bug.
- **`README.md`:** one line added pointing to `FEATURES.md`.

When a command is added, renamed or removed, `FEATURES.md` needs updating and the check rerun.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI

- Read `FEATURES.md` first: every command, what it does, its code path and status. Don't re-explore.
- `notes.json` is the owner's real data. Never run `add`/`purge` against it; use a repo copy or the
  `tests/conftest.py` fixture, which points `store.PATH` at a temp file.
- Tests: `python -m pytest tests -q`. Checks per feature: `VERIFY.md`.
- After adding/renaming/removing a subcommand, update `FEATURES.md` and run
  `python <feature-map skill>/scripts/features.py check --strict`.
- Known bug: `sync` is declared but has no handler and crashes.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how to reach each feature. Run everything as `python notes.py <command>`
from this folder. `features.py check` tests every entry point here against the code.

**Data warning:** every command reads and writes `notes.json` next to `store.py` (the owner's real
notes; the path is fixed in `store.PATH`). To try a command that writes (`add`, `purge`), run a copy of
the repo, or patch `store.PATH` the way `tests/conftest.py` does. Tests: `python -m pytest tests -q`.

## Add
- what: Save a new note with a title, a body and any number of tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends `{id, title, body, tags}` to notes.json; id = highest existing id + 1
- usage: `python notes.py add "<title>" "<body>" [--tag T]...` (repeat `--tag` for several)
- verify: Add
- status: proven: ran `add` on a temp copy of the repo (prints `added #4`); tests/test_add.py

## List
- what: Print every note as `#id title  [tags]`, or only those carrying one tag.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- usage: `python notes.py list [--tag T]` (read-only)
- verify: List
- status: proven: ran `list --tag home`, got #1 and #3; tests/test_list.py

## Search
- what: Find notes whose title or body contains a phrase (case-insensitive); prints `#id title`.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- usage: `python notes.py search "<text>"` (read-only; tags are not searched)
- verify: Search
- status: proven: ran `search dune`, got `#3 Books`; tests/test_search.py

## Export
- what: Write all notes to a JSON file of your choosing, as a backup or for another tool.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates or overwrites the file at the given path; notes.json is only read
- usage: `python notes.py export <path>`
- verify: Export
- status: proven: ran `export` to a file outside the repo, contents equal notes.json; tests/test_export.py

## Purge
- what: Delete every note at once; refuses (exit 1) unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`; there is no undo, so export first
- usage: `python notes.py purge --yes`
- verify: Purge
- status: traced: read the whole chain; not run on the real data (it deletes everything); tests/test_purge.py covers it on a temp copy

## Not features
- cli: `sync` @ notes.py: declared in the parser ("sync notes with the cloud") but has no entry in `HANDLERS`; running it crashes with `TypeError: 'NoneType' object is not callable` (exit 1)

## Not built
Cloud sync: only the `sync` subcommand name exists (see above). There is no edit or delete-one-note
command, and tags are not searched.


<!-- file written by the agent: fixture/VERIFY.md -->
require: challenge

## Add
- path: notes.py, store.py, commands/add.py
- test: `python -m pytest tests/test_add.py -q`
- oracle: tests/conftest.py
- fail-signal: expected 'added #4'
- fail-proof: challenge: next id `+ 1` -> `+ 2` in commands/add.py, test_add went red, reverted

## List
- path: notes.py, store.py, commands/listing.py
- test: `python -m pytest tests/test_list.py -q`
- oracle: tests/conftest.py
- fail-signal: expected only home notes listed
- fail-proof: challenge: tag filter `in` -> `not in` in commands/listing.py, test_list_by_tag went red, reverted

## Search
- path: notes.py, store.py, commands/search.py
- test: `python -m pytest tests/test_search.py -q`
- oracle: tests/conftest.py
- fail-signal: expected body match
- fail-proof: challenge: dropped body match in commands/search.py, test_search went red, reverted

## Export
- path: notes.py, store.py, commands/export.py
- test: `python -m pytest tests/test_export.py -q`
- oracle: tests/conftest.py
- fail-signal: expected exported file to equal all notes
- fail-proof: challenge: exported `store.all()[1:]` in commands/export.py, test_export went red, reverted

## Purge
- path: notes.py, store.py, commands/purge.py
- test: `python -m pytest tests/test_purge.py -q`
- oracle: tests/conftest.py
- fail-signal: expected empty store after purge
- fail-proof: challenge: purge kept the first note in commands/purge.py, test_purge_yes_deletes_all went red, reverted

## Blind spots
- `sync` (in notes.py) has no handler and crashes; there is no feature to check (see FEATURES.md, Not features)
