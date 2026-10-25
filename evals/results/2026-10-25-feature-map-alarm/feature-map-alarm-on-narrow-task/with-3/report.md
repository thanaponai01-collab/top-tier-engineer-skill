The repo now calls the command `mood` everywhere, and your `notes.json` is byte-for-byte unchanged (I compared it against a backup after every step).

**Rename changes:**
- `features/fields-text-1.md`: the Mood field entry now reads `cli: \`mood\` @ notes.py`.
- `commands/fields/mood.py`: the docstring lists `mood` instead of `show-mood`.
- `.features/mood-field.json`: I ran `python notes.py mood 1` against your notes (it only reads, giving `#1 mood: calm`) and recorded it as the new receipt. The old `show-mood` receipt was dropped. Every other recorded run was re-recorded with `prove --again`; all the commands that write ran in a throwaway copy, never against your file.

**Three other commands are broken, and the rename didn't cause it.** The check found they fail now although they passed when first recorded. I didn't change that code. As `AGENTS.md` asks, I set those features' status to `failing` in the map:
- **`count-owner`** crashes with `TypeError` when sorting values where some notes have no owner (`commands/fields/owner.py:51`).
- **`by-rating 4`** rejects 4 with "rating must be 1-5".
- **`clear-sprint`** crashes with `KeyError: 'sprint'` because it reads the field after removing it (`commands/fields/sprint.py:35`).

The final check reports 0 stale, 0 drifted, 0 unproven and 0 regressed. A backup of your notes is at `notes.backup.json`, one folder above `fixture/`. Delete it whenever you like. I left the old `_work/` copy alone; it still mentions `show-mood`. I can fix the three broken commands if you'd like.