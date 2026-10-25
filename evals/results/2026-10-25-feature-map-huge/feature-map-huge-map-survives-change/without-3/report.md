I've updated `fixture/CLAUDE.md` to match what the CLI actually does now. There's no git history, so I worked out the changes by comparing each field module against the `area.py` template and the argparse wiring in `notes.py`. I confirmed every one by running it against a scratch copy of the notes.

**What changed in the CLI** (every other field module is still an exact copy of the template):

1. **`show-mood` was renamed to `mood ID`.** `show-mood` is now an invalid command (exit 2). The other 24 fields still have `show-F`.
2. **`set-rating` rejects every valid value.** The range check is backwards: 1–5 is refused with "rating must be 1-5", and values like 0 or 7 are accepted and saved.
3. **`count-owner` crashes.** It now sorts by the raw value instead of `str(value)`, so it throws a `TypeError` when any note has no owner. Your current notes have one, so it fails today.
4. **`clear-sprint` changes your data and then crashes.** It no longer sets sprint to `null`. It deletes the `sprint` key, moves the old value into a new `history` list on the note, saves, and then fails with a `KeyError`. The traceback hides that the change was already written.

**What I changed in the doc:**
- Added the `mood` exception and a "Broken / divergent field commands" section covering items 2–4.
- Marked the general rules for `clear-F` and `count-F` as having exceptions, and added `mood` to the list of read-only commands.
- Fixed the exit-code note: crashes exit 1 and bad commands exit 2. It used to say everything else exits 0.

**Your notes:** I never wrote to the real `notes.json`; its checksum was identical before and after. I deleted the scratch copy and the `__pycache__` folders afterwards. `README.md` needed no change.

I only updated the docs and didn't fix the code. Items 2–4 look like bugs rather than intended changes, so check with your teammate. Until then, avoid `clear-sprint` on the real notes. I can fix them if you want.