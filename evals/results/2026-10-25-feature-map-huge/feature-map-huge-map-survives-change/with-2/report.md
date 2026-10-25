The docs now match what the CLI actually does. A full re-check shows 0 stale, 0 unmapped, 0 drifted and 0 regressed. Your `notes.json` hasn't changed: its checksum is the same as before I started. Everything that writes data ran only in throwaway copies or a scratch directory.

The teammate's push changed four things. Three of them are bugs, which I've written down as `failing` rather than fixed:

1. **Rating (`set-rating`, `by-rating`)**: the 1–5 range check in `commands/fields/rating.py` is backwards. Valid ratings like `set-rating 1 3` are rejected with "rating must be 1-5" (exit 1), while out-of-range values like `9` or `0` are accepted and saved.
2. **Sprint (`clear-sprint`)**: this one can damage data. It removes the `sprint` key, moves the old value into a new `history` list on the note, saves the file, and only then crashes with `KeyError: 'sprint'`. So the change is written even though the command reports failure (exit 1).
3. **Owner (`count-owner`)**: it crashes with `TypeError` whenever any note has no owner. It sorts the raw values instead of converting them to strings first, like every other field does. It still works if every note has an owner.
4. **Mood**: `show-mood` was renamed to `mood ID`. `show-mood` is now an "invalid choice" error. This one works fine; it's just a rename, so I mapped it and recorded a passing run.

Everything else (the core commands and the other 21 fields) re-ran with the same results as before.

**Files changed:**
- `features/fields-numbers.md`: rating and sprint now say what actually happens and are marked failing.
- `features/fields-people.md`: owner's `count-owner` marked failing.
- `features/fields-personal.md`: the show command is now `mood`, and the rename is noted.
- `.features/*.json`: every run re-recorded. The four failing runs are recorded as failures, not as proof.

I didn't touch the teammate's code. Each bug is a one-line fix:
- **Rating:** change `if 1 <= v <= 5` to `if not 1 <= v <= 5`.
- **Sprint:** print the old value before popping it.
- **Owner:** sort with `key=lambda kv: str(kv[0])`.

Until then, don't run `clear-sprint` on your real notes. Want me to apply the fixes?