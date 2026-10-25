`python .features/features.py check --rerun` re-ran all 133 recorded runs; four changed:

- `show-mood` was renamed `mood` (`show-mood` is now an invalid choice). Map updated.
- `set-rating` is broken: `set-rating 1 4` exits 1 with "rating must be 1-5"; the new check is inverted.
- `count-owner` is broken: TypeError comparing str and None in its sort.
- `clear-sprint` is broken: KeyError: 'sprint' after it pops the field.

The other 129 re-ran as recorded. Writes ran in a throwaway copy; your notes are untouched.
