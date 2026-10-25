I wrote `fixture/FEATURES.md`, a feature map the next session can read instead of exploring the code again. It checks clean: `features.py check --strict` exits 0 with nothing stale, broken, unmapped or unproven. Your real `notes.json` was not changed; its hash was the same before and after.

**What's in the map** (`python notes.py <command>`):

| Feature | What it does | Status |
|---|---|---|
| Add | Saves a note with a title, body and optional `--tag`s | proven: run against a temp copy of `notes.json`, printed `added #4` |
| List | Lists notes, optionally only those with one `--tag` | proven (only reads) |
| Search | Finds notes whose title or body contains the text, ignoring case | proven: `search dune` found #3 |
| Export | Writes all notes to a JSON file at the path you give | proven: exported to a temp file outside the repo |
| Purge | Deletes every note, and refuses without `--yes` | read through the code only, not run, because it deletes data |

Each feature also lists the files its command passes through, from `notes.py` to the command's file to `store.py`, so the next agent doesn't have to search. The run records are in `fixture/.features/*.json`. If any of those files change later, `check` will flag that feature until it is run again.

**Problem found: `sync` doesn't work.** `python notes.py sync` appears in `--help` as "sync notes with the cloud", but it crashes with `TypeError: 'NoneType' object is not callable`. That's because it has no entry in `HANDLERS` in `notes.py`, and there is no sync code anywhere. I put it under "Not features" with that reason and noted cloud sync under "Not built", so it isn't listed as working. I didn't change the code. You can either add a handler or remove the subcommand.

There's no `VERIFY.md` in the repo, so the map has no links to one and I didn't create one. After any change that adds, renames or removes a command, run `python <feature-map skill>/scripts/features.py check --strict` to keep the map current.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What `notes` (a note-taking CLI) can do and how to reach each feature. Run as
`python notes.py <command>`; dispatch is the `HANDLERS` dict in notes.py. All notes live in
`notes.json` beside store.py (the owner's real notes: run writing commands against a copy, by
setting `store.PATH` to a temp file, as the receipts in `.features/` did). Check this map with
`python <feature-map skill>/scripts/features.py check --strict`.

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends a note to notes.json with id = max id + 1; `--tag` repeatable.
- status: proven: ran `add` against a temp copy of notes.json, printed `added #4`

## List
- what: Show every note's id, title and tags, optionally only those with one tag.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `list` and `list --tag home` on notes.json (read-only)

## Search
- what: Find notes whose title or body contains a text, case-insensitive.
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: ran `search dune`, found #3 Books (read-only)

## Export
- what: Write all notes to a JSON file at a path you give.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the file at `path`; notes.json is only read.
- status: proven: ran `export` to a temp file outside the repo

## Purge
- what: Delete every note; refuses unless `--yes` is given.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- needs: `--yes` (without it prints `refusing without --yes`, exit 1)
- effect: overwrites notes.json with `[]`. Destructive: not run.
- status: traced: read notes.py > commands/purge.py > store.save; not run because it deletes data

## Not features
- cli: `sync` @ notes.py: declared in the parser ("sync notes with the cloud") but has no entry in `HANDLERS`; `python notes.py sync` crashes with `TypeError: 'NoneType' object is not callable` (seen 2026-10-25)

## Not built
- Cloud sync: only the `sync` subcommand stub exists; no sync code anywhere.
