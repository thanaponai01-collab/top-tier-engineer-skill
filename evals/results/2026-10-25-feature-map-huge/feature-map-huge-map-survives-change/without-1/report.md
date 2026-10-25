I updated `fixture/CLAUDE.md` (the repo's reference doc for this CLI) to match what the code does now. I checked each claim by running the commands on a throwaway copy in `/tmp`, never on your real notes. `fixture/notes.json` is unchanged and still loads as valid JSON. `README.md` didn't need changes. I didn't fix any of the code; this pass only corrects the docs.

**What the teammate changed:**

1. **New field `risk`.** It's a plain text field with the usual five commands (`set-risk`, `clear-risk`, `by-risk`, `count-risk`, `show-risk`), and your notes already use it. The old doc said "25 fields" but only listed 24; with `risk` there really are 25.
2. **`show-mood` was renamed to `mood ID`.** `show-mood` now fails with "invalid choice".
3. **`rating` validation is backwards.** `set-rating 1 4` (or any value from 1 to 5) is rejected with "rating must be 1-5", while 0, 9 and other out-of-range values are saved. `by-rating` has the same problem.
4. **`count-owner` crashes** with a `TypeError` whenever any note has no owner. That's already the case in your notes (note #1), so this command doesn't work today.
5. **`clear-sprint` is broken in a way that changes data.** Instead of emptying `sprint`, it deletes the field, copies the old value into a new `history` list on the note, saves, and *then* crashes with a traceback. So it looks like it failed, but the change has been written. If the note has no `sprint` field, it crashes before saving and nothing changes.

**Smaller corrections to the doc:**
- `debug-dump` was described as hidden from `--help`. It has no description, but it does appear in the list of commands.
- The exit codes are now accurate: a rejected rating exits 1 and command-line errors exit 2, not "everything else exits 0".
- The command count is 133 (8 core commands plus 5 per field), not "about 125".

These bugs are listed under a new "Broken commands" section so nobody relies on them. Until they're fixed, avoid running `clear-sprint` on your real notes, because it changes them even when it looks like it failed. I can fix the three bugs (`rating`, `count-owner`, `clear-sprint`) next if you'd like.