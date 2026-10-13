The current owner requirement is 500 rows (brief/export.md); app.py still permits 1000.
Git's "Bound exports after memory pressure" commit explains the older allocation limit.
The oversized-request message wording remains open (work/export.md).
`python -m unittest test_limits` fails above the new limit; the 2026-10-10 passing receipt is historical.
Next: reconcile the boundary and preserve the unresolved message question. No files were changed.
