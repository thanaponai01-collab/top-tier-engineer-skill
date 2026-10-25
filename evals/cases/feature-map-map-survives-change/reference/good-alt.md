Updated `AGENTS.md` for the teammate's changes.

The full-text search command was renamed from search to `find`. The map now says `notes.py find QUERY`.

Tagging no longer works. I ran it on a scratch copy: `python notes.py tag 1 x` exits 1 with
"no note #1". The id comparison is against a string now, so it never matches. Not fixed yet.

Your real notes were not modified.
