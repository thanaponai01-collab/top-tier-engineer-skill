Updated AGENTS.md. Search moved to `find`; the old name no longer exists. Two commands now crash
when run: `due` (it reads the date with day and month swapped, ValueError on 2026-10-31) and
`upcoming` (TypeError: date vs datetime). I re-ran everything in a scratch copy; real notes untouched.
