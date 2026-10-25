I've updated the repo for the rename. The feature check now passes with nothing stale, drifted or unproven. `fixture/notes.json` was never written to; its hash is the same before and after.

**Rename changes**
- `features/fields-text-m-z.md`: the map line for Field mood now reads `` cli: `mood` @ notes.py `` instead of `show-mood`.
- `commands/fields/mood.py`: the comment at the top now lists `mood` instead of `show-mood`.
- `.features/field-mood.json`: I ran `python notes.py mood 1` to record proof that the new command works, and the old `show-mood` record was dropped automatically. The command only reads your notes and printed `#1 mood: calm`.
- `README.md` and `FEATURES.md` didn't mention the command, so they needed no change.

**Three other commands are broken now**
AGENTS.md says to re-run every recorded command after a change. When I did, three commands that used to pass now fail. The rename didn't cause this. I changed their status from `proven` to `failing: …` in the map, as AGENTS.md says to, but I didn't change their code:
- **Field rating:** `set-rating 1 3` and `by-rating 3` reject 3 with "rating must be 1-5", even though 3 is in range. The range check looks wrong.
- **Field sprint:** `clear-sprint 1` crashes with `KeyError: 'sprint'` on a note that has no sprint set (`commands/fields/sprint.py:35`).
- **Field owner:** `count-owner` crashes with a `TypeError` when some notes have no owner (`commands/fields/owner.py:51`). `mood.py` avoids this by sorting with `str(kv[0])`.

These look like recent edits, maybe from the same teammate. I can fix them if you want.