Wrote `FEATURES.md`: 5 working features, 1 broken, 1 internal command. Every way in is
`python notes.py <cmd>`, dispatched by `HANDLERS` in `notes.py`.

## Add, list, search, tag
- add / list / search / tag: `notes.py <cmd>` -> commands/<cmd>.py -> store.py. proven: ran each on a
  copy of notes.json.

## Export
- cli: `export PATH` @ notes.py -> `run` @ commands/export.py
- status: **broken**. Running it crashes with `ValueError: dict contains fields not in fieldnames:
  'tags'`: the DictWriter only lists id, title, body. Reading the code it looks fine.

## Purge
- cli: `purge --yes` @ notes.py -> commands/purge.py -> `save([])` @ store.py
- status: **traced, not run**. It wipes the real notes.json; only the refusal (no `--yes`, exit 1)
  was run.

## Not features
- `debug-dump`: internal dump of notes.json, listed in help with no description.
