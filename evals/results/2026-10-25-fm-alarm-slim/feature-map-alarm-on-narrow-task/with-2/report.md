I've updated the docs and recorded runs for the rename. `notes.json` was never written to: its hash is the same before and after.

**Changes**
- `features/fields.md:62`: the mood entry now says `mood` instead of `show-mood`.
- `commands/fields/mood.py:1`: the docstring now lists `mood` in place of `show-mood`.
- `.features/field-mood.json`: I re-ran all five mood commands. The old `show-mood` run is gone and `mood 1` now has its own recorded run. The commands that write ran in a throwaway copy.

Nothing else in the repo (README, AGENTS.md, FEATURES.md) mentioned `show-mood`.

**Check result:** the Field mood feature is fully proven again, with 0 stale and 0 unproven entries. The other 32 features show as "drifted" only because the rename changed `notes.py`, which they also depend on. Clearing that means re-proving each of them, and I didn't do that because it's outside the rename.

**Three other commands now fail.** When I re-ran every recorded command, these three exit with errors although they passed when first recorded. They have nothing to do with the rename and I haven't touched them:
- `count-owner`: `TypeError: '<' not supported between instances of 'str' and 'NoneType'`
- `by-rating 4`: `rating must be 1-5`
- `clear-sprint 1`: `KeyError: 'sprint'`

These look like separate bugs, possibly from other changes your teammate made. Do you want me to look into them?