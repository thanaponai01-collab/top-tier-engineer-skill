Slice 4 is done and proven: `python cli.py export out.json --month 2026-09` writes JSON holding
INV-103 and INV-104, and the full export still writes all four. Tests: 2 passed, including a new
month test that failed before the change.

The format change is recorded so it survives this session. In BRIEF.md's decisions section the CSV
line is replaced by "Export format is JSON only ... replaces CSV (2026-09-02)", and the old line is
in BRIEF.archive.md with the date it was retired. CLAUDE.md now has a short start-here block that
sends a fresh session to BRIEF.md first. CSV is gone from the code entirely.

Not committed, as asked; BUILD.md marks the slice uncommitted.
