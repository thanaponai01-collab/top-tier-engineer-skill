I've updated `fixture/CLAUDE.md` to match how the tool works now. To check it, I ran every command in a throwaway copy of the folder, so your real `notes.json` was never touched. It's byte-for-byte the same as before, and I didn't leave any stray files in `fixture/`.

**What the teammate changed:**

1. **`search` is now called `find`.** `python notes.py find QUERY` behaves the same as before. Typing `search` now fails with an "invalid choice" error. The code is still in `commands/search.py`.
2. **`tag` is broken.** It always prints `no note #ID` and fails, even for notes that exist, so it never saves a tag. The cause is in `commands/tag.py`: it compares each note's id, which is a number, against the id you typed after turning it into text, so they never match. Until it's fixed, the only way to tag a note is `add ... --tag T` when you create it. I wrote this up in the doc as a known problem; I didn't change the code.
3. **`purge --yes` prints a different message.** It now prints `all notes deleted`. The line it adds to `purge.log` is still `purged all notes`.
4. **One small correction:** the doc said `debug-dump` was hidden from `--help`. It has no description line there, but it does still appear in the list of commands.

Everything else still matches the doc: `add`, `list`, `export` (which still silently overwrites the file), the `purge` safety check without `--yes`, and the warning about the CSV export. Cells starting with `=` are still written as-is, so a spreadsheet may treat them as formulas. I left `README.md` alone because nothing in it is wrong.

To fix `tag`, change the comparison to `n["id"] == args.id`. I can make that change if you want, or leave it for the teammate.