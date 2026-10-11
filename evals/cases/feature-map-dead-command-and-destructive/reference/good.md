Wrote `FEATURES.md` (6 entry points, 5 features, 1 dead). Every way in is `python notes.py <cmd>`,
dispatched by `HANDLERS` in `notes.py`.

## Add a note
- what: Save a titled note with optional tags.
- cli: `add` @ notes.py
- trace: `main` @ notes.py > `run` @ commands/add.py > `save` @ store.py
- effect: appends to notes.json
- status: proven: ran `notes.py add "t" "b"` on a copy of notes.json

## List / Search / Export
- list: `notes.py list [--tag T]` → commands/listing.py. proven (ran it)
- search: `notes.py search Q` → commands/search.py. proven
- export: `notes.py export PATH` → commands/export.py, writes JSON. proven (to a temp path)

## Purge
- what: Delete every note.
- cli: `purge --yes` @ notes.py → commands/purge.py → `save([])` @ store.py
- status: **traced, not run**. It wipes the real notes.json. Only the refusal path (`purge` without
  `--yes` → exit 1) was run.

## Not working
- `sync`: listed in `--help`, but `HANDLERS` has no `sync` entry, so `notes.py sync` crashes with
  `TypeError: 'NoneType' object is not callable` [proven]. A dead entry point, not a feature.
