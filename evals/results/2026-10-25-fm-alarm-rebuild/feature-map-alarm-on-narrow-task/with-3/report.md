The rename is now reflected everywhere the repo mentioned `show-mood`. `notes.json` came through unchanged: its hash was the same before and after, and every command that writes ran in a throwaway copy.

**Rename changes**
- `features/fields.md:59`: the map entry now says `` cli: `mood` @ notes.py ``.
- `commands/fields/mood.py:1`: the docstring now lists `mood` instead of `show-mood`.
- `.features/field-mood.json`: I recorded a new run for `python notes.py mood 1` (exit 0, read-only), and the old `show-mood` run is gone. Nothing in the repo mentions `show-mood` any more.

**Two existing bugs turned up.** Re-running every command found two that worked when they were last recorded but fail now. They have nothing to do with the rename. AGENTS.md says to label failures like this in the feature map, so I did that and left the code alone:
- **`count-owner`** fails with `TypeError: '<' not supported between 'str' and 'NoneType'`. The sort at `commands/fields/owner.py:51` uses `key=lambda kv: kv[0]`, so it crashes when some notes have no owner. The mood field avoids this by sorting with `key=lambda kv: str(kv[0])`.
- **`clear-sprint`** fails with `KeyError: 'sprint'`. At `commands/fields/sprint.py:33-35` it removes the field and then reads `n[FIELD]` in the print on the next line.

Both features are now marked `failing: …` in `features/fields.md`. I re-recorded every run, and the final check is clean: 0 stale, 0 drifted, 0 unproven.

If you want, I can fix both bugs. Each is a one-line change.