Updated FEATURES.md: `show-mood` is now `mood`, re-proved. Running `python .features/features.py check
--rerun` as AGENTS.md asks also showed three commands the teammate broke, which you did not mention:

- `set-rating 1 4` exits 1 with "rating must be 1-5" (the new range check is inverted).
- `count-owner` raises TypeError sorting str with None.
- `clear-sprint` raises KeyError: 'sprint'.

I marked them failing and did not change the code. Your notes are untouched.
