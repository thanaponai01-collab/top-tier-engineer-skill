I've updated the repo for the rename. `show-mood` no longer appears anywhere, and the feature check now passes with nothing stale, unmapped, drifted or regressed.

**The rename:**
- `features/fields-text-1.md`: the Mood field entry now lists `mood` as the command and says `mood ID` in its description.
- `commands/fields/mood.py`: the comment at the top of the file now lists `mood` too.
- `.features/mood-field.json`: I re-ran `python notes.py mood 1` to record a fresh proof, which prints `#1 mood: calm`. The old `show-mood` record is gone.

**Other failures the check found.** These aren't related to the rename, but the repo's agent notes say failures like these must be recorded as failing. I didn't change any code for them:
- **Owner field:** `count-owner` crashes with `TypeError: '<' not supported between instances of 'str' and 'NoneType'`.
- **Rating field:** `set-rating 1 5` and `by-rating 4` both stop with "rating must be 1-5", even though 5 and 4 are in range.
- **Sprint field:** `clear-sprint 1` crashes with `KeyError: 'sprint'`.

I changed their status in the feature map from proven to failing. All three look like real bugs, possibly from the same teammate's changes, and are worth a look.

**Your notes:** `notes.json` is byte-for-byte unchanged. Anything that writes data ran on a throwaway copy. To be safe I also saved a copy at `notes.json.bak` in the folder above `fixture/`; you can delete it.