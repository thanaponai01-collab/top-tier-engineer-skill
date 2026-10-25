`FEATURES.md` now matches how the CLI behaves. I ran every command in a throwaway copy. Your `notes.json` was never written to: its hash is the same as before I started, and a backup is in `backup/notes.json.bak`.

**What changed in the teammate's push**

1. **`search` was renamed to `find`.** `python notes.py search dune` now fails with "invalid choice". `find dune` and `find MILK` work as before: they match the title or body, ignoring case. I updated the Search section to say `find` and noted the old name.

2. **`tag` is broken.** It prints `no note #<id>` and exits 1 for every id, including ones that exist like `tag 1 urgent`, and it changes nothing. The cause is in `commands/tag.py:4`: it compares the note's id, a number, with `str(args.id).strip()`, which is text, so they never match. In the docs I marked Tag as **suspected / broken**, wrote down the cause, and recorded the failing run instead of the old success. I didn't change the code since it's your teammate's. The fix is a one-line change to `if n["id"] == args.id:`. Want me to make it?

3. **No other behaviour changed.** I checked by hand:
   - `add` prints "added #4".
   - `list` and `list --tag home` print the expected notes.
   - `export` writes a CSV with columns id,title,body,tags, and tags joined with `;`.
   - `purge` refuses without `--yes`; with it, it writes a line to `purge.log` and empties the notes.
   - `debug-dump` is still hidden from `--help`.

**Docs and checker**
- I re-recorded the proof run for each feature (the write commands only in a copy) and replaced the stale `search` record.
- `python .features/features.py check --strict --rerun` now passes: 0 stale, 0 drifted, 0 regressed.
- Before my update, the checker still showed `search` as "ok" even though the command no longer worked. It just looks for the word in `notes.py`, which also contains `import ... search`. Only re-running the old commands caught it, so keep using `--rerun`.
- `README.md` doesn't name any commands, so it needed no change.