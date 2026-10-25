The map is in `docs/FEATURES.md`. All commands go through `python notes.py`.

- add, list, search and tag work: I ran each one against a scratch copy of the notes.
- export does not work: `python notes.py export /tmp/x.csv` exits 1 with a traceback, because the
  notes have a tags field the CSV writer was not given. I listed it as broken, not as a feature.
- purge I did not run with --yes, since it deletes the real notes; it is marked traced from reading
  purge.py and store.py.
- debug-dump is a developer command, noted separately.
