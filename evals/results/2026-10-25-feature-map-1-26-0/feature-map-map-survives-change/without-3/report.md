I updated `fixture/CLAUDE.md` to match how the CLI behaves now. I ran every command in a throwaway copy of the repo. Your real `notes.json` was never touched: its checksum is the same before and after.

**What changed in the CLI:**

1. **`search` was renamed to `find`.** `notes search milk` now fails with "invalid choice" (exit 2). `find` works the same way the old `search` did: it ignores case and checks only the title and body.
2. **`tag` is broken.** It always prints `no note #N` and exits 1, even for ids that exist, and it changes nothing. In `commands/tag.py` it compares the number id stored in the notes to a text version of the id you type, so nothing ever matches. I wrote this down as a known bug and didn't fix the code, since you only asked about the docs. The fix is one line (`if n["id"] == args.id:`) if you want me to make it.

**Things the docs had wrong or left out:**

- **`debug-dump`:** the docs called it "hidden from `--help`". It has no description there, but it does appear in the list of commands on the usage line.
- **Ids after a purge:** after `purge --yes`, the next note you add is `#1` again. This is now noted.
- **`python -I`:** running the CLI with this flag breaks it (`import store` fails), so I added a warning.

All the other commands (`add`, `list --tag`, `export`, `purge` and its `purge.log` line) behave as the docs already said. `README.md` doesn't name any specific commands, so it needed no changes.