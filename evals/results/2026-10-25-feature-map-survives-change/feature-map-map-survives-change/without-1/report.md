I updated `fixture/AGENTS.md` so it matches how the CLI behaves now. `CLAUDE.md` just pulls in `AGENTS.md`, and the README doesn't name any commands, so neither needed changes. I tested every command on a throwaway copy of the folder, not in the repo. Your real `notes.json` wasn't touched: its checksum is the same as before.

**What changed in the CLI:**

1. **`search` is now called `find`.** Same matching as before (title and body, ignoring case, tags not searched). Running `notes search …` now fails with "invalid choice" (exit code 2), so any scripts or habits that use `search` need updating.
2. **`tag` is broken.** It always prints `no note #ID` and exits with code 1, even for notes that exist, and it saves nothing. I tried `tag 1 x` on the copy and got that error. The cause is in `commands/tag.py`: it compares the note's numeric id to a text version of the id you typed (`str(args.id)`), so they never match. Right now there's no way to add a tag to an existing note. I recorded this in the docs but didn't fix the code, since you asked for the docs to be brought up to date. The fix is to compare `n["id"] == args.id`, and I can make that change if you want.

**Correction to the docs:** they said `debug-dump` wasn't shown in `--help`. It still has no description line, but it does appear in the list of commands on the usage line. I reworded that entry.

Everything else still works as written: `list`, `add` (including more than one `--tag`), `export` (columns `id,title,body,tags`, tags joined with `;`), and `purge` (still refuses without `--yes`). The CSV-injection risk in `export` is still there too. I also added a "last checked 2026-10-25" line to the top of the doc.