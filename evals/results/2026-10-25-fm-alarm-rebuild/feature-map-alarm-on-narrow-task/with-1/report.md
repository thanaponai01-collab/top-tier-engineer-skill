I've updated the repo for the rename from `show-mood` to `mood`. Your notes are safe: `fixture/notes.json` has the same hash after all the runs as before I started.

**Rename changes:**
- `features/fields.md:64`: the feature map entry now reads `` cli: `mood` @ notes.py ``.
- `commands/fields/mood.py:1`: the docstring now lists `mood` instead of `show-mood`.
- I ran `python notes.py mood 1` once to record it (it only reads, and printed `#1 mood: calm`). This replaced the old `show-mood` record in `.features/field-mood.json`.

Nothing else in the repo mentioned `show-mood`. The README and top-level FEATURES.md don't name it.

**Three other commands are broken.** These failures aren't caused by the rename. When I re-checked every command as AGENTS.md says to, three that used to pass now fail. I didn't fix the code. Following AGENTS.md, I changed their entries in `features/fields.md` from `proven` to `failing`, with the error:
- `count-owner` crashes with `TypeError: '<' not supported between instances of 'str' and 'NoneType'`. It looks like it can't sort when some notes have no owner.
- `by-rating 4` rejects the value with `rating must be 1-5`.
- `clear-sprint 1` crashes with `KeyError: 'sprint'`.

I then re-recorded every command's run (`prove --again`). Commands that write data ran in a throwaway copy, as before. The final check reports nothing stale, drifted, unproven or regressed.

Before starting I saved a copy of your notes at `notes.json.bak`, one level above `fixture/`. You can delete it.

Do you want me to fix those three bugs?