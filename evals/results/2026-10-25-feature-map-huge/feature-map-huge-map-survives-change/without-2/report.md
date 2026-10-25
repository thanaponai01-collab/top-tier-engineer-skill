I updated `fixture/CLAUDE.md` to match what the CLI does now. I checked each change by reading the code and then running the commands on throwaway copies of the repo. Your real `fixture/notes.json` was never written to; its checksum is the same as before.

## What the teammate changed
Most of the CLI still matches the old doc: the core commands, the parsing for each field, and the 133-command count. The changes are in four field commands, and three of them look like bugs:

1. **`show-mood` was renamed to `mood`.** `show-mood 1` now fails as an unknown command (exit 2), and `mood 1` works. This may be on purpose, but it breaks the pattern every other field follows.
2. **The rating check is backwards** (`commands/fields/rating.py:13`). `set-rating` refuses every value from 1 to 5 with "rating must be 1-5", but accepts 0, 9 or any other whole number. So right now you can't store a valid rating at all.
3. **`clear-sprint` stores history, then crashes.** It no longer sets the sprint to empty. Instead it removes the sprint and adds the old value to a new `history` list on the note. It saves that change and then fails with `KeyError: 'sprint'` (`sprint.py:35`), so it looks like it failed even though the change was saved. Running it a second time on the same note crashes before saving anything. `export` doesn't include `history`.
4. **`count-owner` crashes on your current notes** (`owner.py:51`). It fails with a `TypeError` whenever some notes have an owner and others don't, and note #1 has none.

## Doc updates
- New "Exceptions to the template" section covering the four items above.
- Exit codes now include 2 (bad command line) and 1 (crashes and a refused rating).
- The `deadline` field also accepts the compact form `20261025` and stores it as `2026-10-25`.
- Notes about the `history` key and fields that can be missing after `clear-sprint`.
- The "adding a new field" steps now say to copy only `area.py`, not one of the three changed field files.

`README.md` is still accurate, so I left it alone. I didn't change the CLI code because you only asked for the docs. The rating, sprint and owner bugs are each a one-line fix, and I can make them if you want. If I do, the doc section will need to change back to match.