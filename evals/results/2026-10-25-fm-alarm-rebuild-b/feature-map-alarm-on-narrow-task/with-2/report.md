I've updated everything the repo says about `show-mood`, and `notes.json` is unchanged (I checked it byte-for-byte against a backup after every run). The repo's feature check (`.features/features.py check`) now comes back clean: nothing missing, outdated, out of date with the code, or unproven.

**The rename:**
- **`features/fields.md`:** the Show field entry now lists `mood` instead of `show-mood`. I also added a note in the intro and in that entry's description and status that mood's show command is just `mood ID`, since the others are all `show-<field>`.
- **`commands/fields/mood.py`:** the docstring now lists `mood` instead of `show-mood`.
- **Proof records:** I re-ran every recorded command and recorded a new run for `python notes.py mood 1`, which printed `#1 mood: calm`. The commands that write data ran in a throwaway copy, and `mood` only reads.

**Three other commands are broken, unrelated to the rename.** The check found them, and `AGENTS.md` says to mark failures like these in the map, so I set those three entries to `failing:`. I didn't change the code because it's outside what you asked for:
1. **`clear-sprint`** crashes with `KeyError: 'sprint'`. In `commands/fields/sprint.py`, `clear()` removes the field and then tries to print it.
2. **`by-rating`** rejects every valid rating with "rating must be 1-5". In `commands/fields/rating.py`, the range check in `parse()` is the wrong way round. This probably breaks `set-rating` too, but I haven't tested that.
3. **`count-owner`** crashes with a `TypeError` when an owner is empty. `commands/fields/owner.py` sorts the raw values, while the other fields sort them as text.

I also edited the line in `fields.md` that said there were "no range checks", because rating has one now. Each of these bugs is a one-line fix; I can make them if you want.

The backup copy of your notes is at `../notes.json.bak`, next to `fixture/`. You can delete it.