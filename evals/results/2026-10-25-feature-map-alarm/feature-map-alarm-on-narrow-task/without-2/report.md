I updated the two places in the repo that still described `show-mood`:

- **`fixture/commands/fields/mood.py`**: the first-line docstring now lists `mood` instead of `show-mood`.
- **`fixture/AGENTS.md`**: the Field commands section says every field `F` has a `show-F ID` command. I added a line saying that for mood the command is `mood ID`, not `show-mood ID`. `CLAUDE.md` just pulls in `AGENTS.md`, so it gets the change too.

The teammate's rename in `notes.py` was already in place, and `README.md` never named the command, so I left both alone.

I tested on a temporary copy of the repo. `mood 1` prints `#1 mood: calm`, and `show-mood` is now rejected as an invalid command. `notes.json` has the same checksum before and after, so your real notes weren't touched.