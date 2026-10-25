The repo's docs now match how the CLI actually behaves. The teammate's changes renamed one command and broke three of the 32 features. I updated the docs to say so but didn't fix the code. Your `notes.json` is byte-for-byte unchanged, and a backup is at `backup/notes.json.bak`.

**What changed**

1. **Renamed:** `show-mood` is now `mood ID`. `show-mood` gives an "invalid choice" error. All the other fields still use `show-<field>`.
2. **Rating is broken:** the 1–5 range check is backwards (`commands/fields/rating.py:12`). Valid ratings like `set-rating 1 4` and `by-rating 4` are rejected with "rating must be 1-5". Out-of-range values like `set-rating 1 7` are accepted and saved. The old passing check for this used 7, so it hid the bug.
3. **`clear-sprint` is broken, and it changes data before failing.** It deletes the note's `sprint` key and adds the old value to a new `history` list. It then saves and crashes with `KeyError: 'sprint'`. So it reports an error even though the file was already changed. Don't run it on your real notes until it's fixed.
4. **`count-owner` is broken:** it crashes with a `TypeError` whenever any note has no owner, which is true of your notes.

Everything else still works: add, list, show, search, tag, export, purge and the other 21 field command sets.

**What I updated**
- In `features/fields-text-m-z.md`, the mood command is now listed as `mood`. Owner is marked failing, with the error.
- In `features/fields-typed.md`, rating and sprint are marked failing, with the errors. The sprint entry also explains what `clear-sprint` now does to the data.
- I re-ran and re-recorded every check, adding a new run for `mood` and a failing run for `set-rating 1 4`. Anything that writes data ran in a throwaway copy. The final check reports no stale, drifted or unmapped commands. The four failing commands are listed under "failing".

All three bugs are small fixes. I can make them if you want, or leave them for the teammate.