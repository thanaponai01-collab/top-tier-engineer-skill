I updated the two places in the repo that still described the old `show-mood` name. Your teammate's code change was already in place (`notes.py:127` registers `mood`), so I didn't touch it.

- **`commands/fields/mood.py`**: the comment at the top of the file now lists `mood (print)` instead of `show-mood`.
- **`AGENTS.md`**:
  - The rule that every field has a `show-F ID` command now notes the exception: for mood it's `mood ID`.
  - `mood` is now in the list of always-safe read-only commands, since the `show-*` pattern no longer covers it.
  - The "133 subcommands" count is still right, because it was a rename, not an added or removed command.

`README.md` and `CLAUDE.md` never mentioned `show-mood`, so they didn't need changes. `notes.json` wasn't touched: I only ran `python notes.py mood --help`, which doesn't read or write notes. It confirmed the new command name works.