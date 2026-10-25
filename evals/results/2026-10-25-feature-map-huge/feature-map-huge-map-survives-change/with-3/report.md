The feature docs now match what the CLI actually does. Your notes in `fixture/notes.json` are byte-for-byte unchanged: I checked against a backup copy after every step and deleted that copy at the end. Anything that writes ran either in a scratch copy or with `--copy`.

## What changed in the teammate's push
Re-running every recorded command showed one renamed command and four broken ones. The other 28 features work as documented.

1. **`show-mood` was renamed to `mood`.** `python notes.py mood ID` works, and `show-mood` now gives an "invalid choice" error. This is the only field that doesn't follow the `show-F` pattern.
2. **Rating's 1–5 check is backwards** (`commands/fields/rating.py`, `parse()`). `set-rating` and `by-rating` reject every value from 1 to 5 with "rating must be 1-5" and accept anything else (7, 0, -3). The old proof used `set-rating 1 7`, which is why it still passed.
3. **`clear-sprint` changes your data and then crashes.** It deletes the note's `sprint` value, adds the old value to a new `history` list, saves, then exits with `KeyError: 'sprint'`. So it looks like it failed when it actually did the change. Running it again on the same note crashes without saving anything.
4. **`count-owner` crashes** with a `TypeError` whenever any note has no owner, which is true of your notes. The teammate changed how it sorts, and empty owners now break it.

These are bugs in the code. I only documented them and didn't fix them. Tell me if you want them fixed; each is a one-line change.

## What I updated
- `features/fields-text-1.md`: the mood entry now uses `mood`, with a note about the exception. Owner is marked `failing` with the error.
- `features/fields-typed.md`: Rating and Sprint are marked `failing`, and the descriptions now say what really happens, including what `clear-sprint` writes.
- `.features/*.json`: I re-recorded every proof and added two new ones, `mood 1` and `set-rating 1 3` (the second shows the failure).

`check --rerun` now finishes clean: nothing out of date or unlisted, and nothing that used to work now fails. I also deleted the `__pycache__` folders Python created during the runs.