Ran `python .features/features.py check --rerun` first. Two things changed since the map was made:

- `search` was renamed: the subcommand is now `find` (`python notes.py find QUERY`); `search` gives
  "invalid choice". I updated FEATURES.md and re-proved it.
- `tag` is broken: its recorded proof passed before and fails now. `tag 1 work` prints `no note #1`
  and exits 1 for every note, because tag.py compares the int id to `str(args.id)`. I marked it
  broken in the map and did not change the code.

Your notes.json is untouched; writes were proven in a throwaway copy.
