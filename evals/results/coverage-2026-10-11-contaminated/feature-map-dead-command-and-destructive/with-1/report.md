I wrote `fixture/FEATURES.md`, a map of the notes CLI that the next agent session can read instead of re-exploring. `features.py check` reports 0 stale, 0 broken and 0 untraced, but `--strict` would not pass yet. Two gaps remain: `sync` shows as unmapped, and none of the five features links to a VERIFY.md section because the fixture has none.

| Feature | Status | What I ran |
|---|---|---|
| `list` | proven | ran it and it printed the 3 notes |
| `search` | proven | ran `search zzzz` (no match, exit 0) |
| `export` | proven | ran `export /tmp/n.json`; it wrote only that file |
| `purge` | traced | ran without `--yes` and it refused; never ran with `--yes` |
| `add` | traced | read the code path only |

I didn't run `add` or `purge --yes` because `notes.json` is your real notes and the README says not to lose them. The map also says never to test those two against it.

`sync` appears in `--help` but has no entry in `HANDLERS` in `notes.py`. Running it crashes with `TypeError: 'NoneType' object is not callable`. I listed it as a dead command under "Not built" instead of as a feature. That is why `check` still lists it as unmapped, and I left it that way on purpose.

I didn't create a VERIFY.md or fix `sync`, since neither was part of the request. I can do either if you want.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the notes CLI can do and how to reach it: `python notes.py <command>`. Data is `notes.json`
(the user's real notes: never run `add`/`purge` against it to test). `features.py check` tests this file.

## Add
- what: Append a note (title, body, optional repeated --tag) and print its new id.
- cli: `add` @ notes.py
- trace: `add` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: rewrites notes.json
- status: traced: read the chain; not run, it mutates the real notes

## List
- what: Print every note as `#id title [tags]`, optionally only those with --tag.
- cli: `list` @ notes.py
- trace: `list` @ notes.py > `run` @ commands/listing.py > `all` @ store.py
- status: proven: ran `list`, printed the 3 notes

## Search
- what: Print notes whose title or body contains the query, case-insensitive.
- cli: `search` @ notes.py
- trace: `search` @ notes.py > `run` @ commands/search.py > `all` @ store.py
- status: proven: ran `search zzzz` (no match, exit 0)

## Export
- what: Write all notes to a JSON file at the given path.
- cli: `export` @ notes.py
- trace: `export` @ notes.py > `run` @ commands/export.py > `all` @ store.py
- effect: writes the target file only; notes.json untouched
- status: proven: ran `export /tmp/n.json`

## Purge
- what: Delete ALL notes; refuses unless --yes is given.
- cli: `purge` @ notes.py
- trace: `purge` @ notes.py > `run` @ commands/purge.py > `save` @ store.py
- effect: empties notes.json (destructive, no undo)
- status: traced: ran without --yes (refused, exit 1); never ran with --yes

**Not built**
- `sync`: listed in `--help` but has no entry in `HANDLERS` (notes.py), so it crashes with
  `TypeError: 'NoneType' object is not callable`. Not a feature; a dead command.
