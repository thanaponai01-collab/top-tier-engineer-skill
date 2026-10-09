Done: exports are JSON now, and `--month YYYY-MM` filters to one month (2026-09 gives the two
September invoices). I added a failing test for the filter first, then made it pass; the suite is green.

So the next session doesn't slide back: I rewrote the format entry in the brief's decisions
(BRIEF.md) to say JSON only, naming the CSV choice it replaces, and moved the retired CSV entry to an
archive file. The project's CLAUDE.md now points straight at BRIEF.md. I did not leave a CSV option
or fallback behind; the csv module is no longer imported.

Nothing committed. BUILD.md lists the slice as proven but uncommitted.
