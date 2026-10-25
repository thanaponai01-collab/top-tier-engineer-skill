`python .features/features.py check --rerun` named three changes since the map was proven:

- `search` was renamed `find` (`search` now gives "invalid choice"). Map updated, re-proved.
- `due` is broken: `due 1 2026-10-31` raises `ValueError: unconverted data remains`, because it
  now parses `%Y-%d-%m`. Marked failing.
- `upcoming` is broken: it raises `TypeError` comparing a date with a datetime. Marked failing.

The other 27 commands re-ran as recorded. Writes ran in a throwaway copy; your notes are untouched.
