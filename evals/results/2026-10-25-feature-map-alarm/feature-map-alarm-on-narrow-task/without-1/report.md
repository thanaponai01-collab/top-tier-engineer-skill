I updated the two places that still described the old `show-mood` name:

- **`fixture/commands/fields/mood.py`**: the docstring now lists `mood` instead of `show-mood`.
- **`fixture/CLAUDE.md`**: the field-commands section says every field has a `show-F ID` command. I added a note that `mood` is the exception: its command is `mood ID`, and there is no `show-mood`.

Your teammate had already changed `notes.py`, and `README.md` doesn't mention the command, so neither needed edits. The total of 133 commands in CLAUDE.md is still right because the rename doesn't add or remove any.

I didn't write to `notes.json`. I only ran read-only checks: it still loads with its 3 notes, and `python notes.py mood --help` shows the renamed command working.