The repo now uses `mood` everywhere it used to say `show-mood`. The code change itself was already in `notes.py`. Your `notes.json` is byte-identical to how it started: I backed it up, compared it after every step, then deleted the backup. Commands that write only ran in throwaway copies.

**What I updated:**
- `features/fields-text-m-z.md`: the entry `cli: show-mood` is now `cli: mood`, and the effect line now lists `mood` among the read-only commands.
- `commands/fields/mood.py`: the docstring's command list says `mood` instead of `show-mood`.
- `.features/mood-field.json`: I ran `python notes.py mood 1`, which exits 0 and prints `#1 mood: calm`, and saved its receipt. The old `show-mood` receipt was dropped. Then I re-recorded every receipt with `prove --again`.

**Separate problem you should know about:** re-running the commands turned up four broken ones that have nothing to do with the rename. They all passed when last recorded, so something changed in the code since then. As `AGENTS.md` asks, I changed their status from `proven` to `failing: <error>`, but I didn't fix the code:
- **`count-owner`** crashes when a note has no owner. It sorts the values, and an empty value can't be compared with text (`commands/fields/owner.py:51`).
- **`set-rating 1 3` and `by-rating 3`** say "rating must be 1-5", even though 3 is in range.
- **`clear-sprint 1`** crashes with `KeyError: 'sprint'` when the note has no sprint (`commands/fields/sprint.py:35`).

After all that, `check --rerun` reports no stale, drifted, unproven or regressed entries. I can fix those four bugs if you want.