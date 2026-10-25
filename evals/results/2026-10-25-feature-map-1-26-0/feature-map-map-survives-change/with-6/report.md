I updated `fixture/FEATURES.md` and the run records in `fixture/.features/` to match how the CLI behaves now. The check (`features.py check --rerun`) now passes cleanly. Your `fixture/notes.json` is unchanged: its checksum is the same before and after. I ran everything that writes data (add, tag, export, purge) in a throwaway copy, and only list and find against the real file.

**What changed in the teammate's push:**

1. **`search` is now called `find`.** `python notes.py find <query>` still works the same way (I ran `find dune` and it printed `#3 Books`; uppercase gives the same result). The old `python notes.py search …` now fails with "invalid choice". I updated the docs to use `find` and removed the old `search` run from the records, since that command no longer exists.
2. **`tag` is broken.** `tag 1 urgent` now prints `no note #1` and fails, even though note #1 exists. The cause is in `commands/tag.py`: it compares the note's numeric id to the id as text, so it never finds a match. I didn't fix the code. FEATURES.md now marks tagging as failing and gives this cause.
3. **add, list, export, purge:** these work as before. `purge` without `--yes` still refuses and deletes nothing.

`README.md` and `AGENTS.md` don't describe these commands in detail, so they needed no changes.

**Decision for you:** the `tag` fix is a one-line change (compare the ids as numbers). Should I make it, or leave it for the teammate?

I also left a safety copy of your notes at `../tte-backup-88/notes.json`, outside `fixture/`. You can delete it.