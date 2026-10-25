The repo now calls the command `mood` everywhere, and `notes.json` hasn't changed. I compared it byte-for-byte against a backup after every run, and all the commands that write data ran in a throwaway copy.

**What I changed**
- `features/fields-text-m-z.md`: the map entry `cli: \`show-mood\`` is now `cli: \`mood\``.
- `commands/fields/mood.py`: the first-line description of the file now lists `mood` instead of `show-mood`.
- `.features/field-mood.json`: I re-ran and re-recorded all five mood commands, so the old `show-mood` record is gone. `python notes.py mood 1` prints `#1 mood: calm`.

**Result:** the check now reports 0 stale and 0 unmapped (before, it reported 1 of each), and all mood commands pass when re-run. `README.md` and `FEATURES.md` didn't mention the command, so they needed no change.

**Other problems the check found, which I left alone:**
- `count-owner`: crashes with `TypeError: '<' not supported between 'str' and 'NoneType'`.
- `set-rating 1 5` and `by-rating 5`: both now fail with "rating must be 1-5", even though 5 is in range.
- `clear-sprint 1`: fails with `KeyError: 'sprint'`.
- 31 other features are marked "drifted" because `notes.py` changed after they were last recorded.

`AGENTS.md` says to finish with `prove --again` across the whole repo. I ran it only for the mood feature, because the full run would overwrite the earlier passing records for those four commands with failing ones, and would mark all the other features as passing against the current code. I can fix those bugs, or mark them `failing:` in the map, if you'd like.