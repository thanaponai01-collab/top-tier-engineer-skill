The repo now calls the command `mood` everywhere, and `show-mood` no longer appears anywhere in `fixture/`. Your notes are safe: `fixture/notes.json` is byte-for-byte the same as before (I backed it up and compared). Commands that change data were only ever run in a throwaway copy.

**What I changed for the rename:**
- `features/fields-text-a.md`: the "Mood field" entry now lists `` `mood` `` as the command, and its usage line now reads `mood ID`.
- `commands/fields/mood.py`: updated the command list in the docstring.
- I ran `python notes.py mood 3` (it only reads) and it printed `#3 mood: calm`. That's now recorded in `.features/mood-field.json`, replacing the old `show-mood` record.

**Something else the check turned up:** after any change, `AGENTS.md` says to run the feature check. It found three commands, unrelated to the rename, that worked when they were last checked and now exit 1:
- `count-owner` crashes with `TypeError: '<' not supported between 'str' and 'NoneType'` (it can't sort counts when some notes have no owner).
- `by-rating 4` is rejected with "rating must be 1-5", even though 4 is in range.
- `clear-sprint 1` crashes with `KeyError: 'sprint'`.

Following `AGENTS.md`, I changed those three entries to `failing: <error>` in `features/fields-text-a.md` and `features/fields-numeric.md`, then ran `prove --again` to re-run and re-record every command. The final check is clean: nothing out of date, unchecked or broken. I didn't fix the three bugs themselves because that's outside the rename. They look like recent edits to `owner.py`, `rating.py` and `sprint.py`, so the teammate may want to look at them.