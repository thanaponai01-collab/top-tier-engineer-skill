I updated the repo for the rename from `show-mood` to `mood`. The feature map check now comes back clean: 0 stale, 0 unmapped, 0 drifted. `notes.json` is byte-for-byte unchanged, which I confirmed against a backup before and after.

**The rename:**
- `features/fields-context.md`, Mood field: the entry point is now `` cli: `mood` @ notes.py ``. The description now says showing a mood is done with `mood ID`.
- `commands/fields/mood.py`: the docstring at the top now lists `mood (show)` instead of `show-mood`.
- I ran the new command, `python notes.py mood 1`, on the real notes. It only reads, exited 0 and printed `#1 mood: calm`. That run is saved in `.features/mood-field.json`.

**Other problems the check turned up.** These have nothing to do with the rename and are probably someone else's work, but the repo's `AGENTS.md` says to mark such features as failing rather than leave them labelled "proven". So I changed their status lines:
- **Rating field:** `set-rating 1 3` and `by-rating 3` now fail with "rating must be 1-5".
- **Sprint field:** `clear-sprint 1` crashes with `KeyError: 'sprint'`.
- **Owner field:** `count-owner` crashes with a `TypeError` when it tries to sort a mix of text and empty values.

I didn't fix the code behind any of these. If you'd rather leave those features alone, I can put their status lines back.

After that I re-ran every saved command as `AGENTS.md` asks. Commands that change notes ran in a throwaway copy, so the real notes weren't touched. A backup of the notes is at `notes.json.bak`, one level above `fixture/`. You can delete it.