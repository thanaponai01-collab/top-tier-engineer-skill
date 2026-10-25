# Notes CLI features

I added FEATURES.md from reading notes.py and the commands folder:

- add: add a note
- list: list notes, optionally by tag
- search: full-text search
- tag: add a tag to a note
- export: writes every note to a CSV file (id, title, body)
- purge: delete all notes

All six commands are wired through HANDLERS and available via `python notes.py`.
