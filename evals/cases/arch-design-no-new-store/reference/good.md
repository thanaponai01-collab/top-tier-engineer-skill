# Design — CSV export + export history

**Structure:** CSV export is a pure function, `reports/export.py:csv_for_report(report)`, called
from the existing `report_detail` view — no new module boundary, since there is exactly one
format. Export history is a new table in the database the app already has (`app/db.py`), not a
new datastore.

**Most expensive decision:** where export history lives. `app/db.py` is already the one owner for
persisted data — `users/models.py` and `reports/models.py` both go through it. Standing up a
separate datastore for a handful of timestamp-and-title rows would be a second thing to back up,
secure and operate, and migrating that history out of it later if the choice turned out wrong is a
real cost. Reusing the existing database is the reversible choice: a table can be added, renamed
or dropped inside the same store with a normal migration.

## Decisions

| decision | options considered | forces | reversibility | evidence |
|---|---|---|---|---|
| where export history is stored | (a) a new table in the existing database via `app/db.py` (b) a separate datastore for "just logs" | only a timestamp and title per row; `app/db.py` already serves reports and users | reusing the database is a two-way door — a migration undoes it; a second datastore is closer to one-way once it holds real history, and is one more thing to back up and secure | traced: `app/db.py:1`, `app/users/models.py:1`, `app/reports/models.py:1` |
| how CSV is produced | (a) Python's stdlib `csv` module in a single function (b) a formatting/export library | one format only, nothing else asked for; a library would use a sliver of itself for ~15 lines of work | two-way door either way — swapping the writer later touches one file | traced: no second format anywhere in `fixture/` |

## Modules

| module | responsibility | owns | must not know |
|---|---|---|---|
| `reports/export.py` (new) | turn one report into a CSV byte string | column order and formatting | how the row got persisted, how the response is built |
| `app/db.py` (unchanged) | the one place that opens a connection and runs queries | the `export_history` table, alongside reports and users | what a caller is exporting |

No plugin, interface or registry for export formats: exactly one format is asked for, and the
stdlib `csv` module already does the job in under 20 lines — a seam earns its place on the second
real implementation, not the first.

## Requirement → structure

- "download as CSV" → `reports/export.py`, called from the existing `report_detail` view.
- "short history of exports" → a new `export_history` table owned by `app/db.py`, the same store
  as everything else.

## Moves

Context: no new datastore, no new service; `app/db.py` stays the only thing that talks to storage.

### 1. Add `reports/export.py`
cost:     nothing today — this is new work, not a fix
files:    `reports/export.py` (new)
owner:    `reports/export.py`
callers:  `reports/views.py:report_detail`
door:     two-way — a pure function, swap it any time
proof:    call `csv_for_report` on a fixture report and diff the output against an expected CSV string
effort:   S
after:    nothing

### 2. Add an `export_history` table via `app/db.py`
cost:     nothing today — this is new work
files:    `app/db.py`
owner:    `app/db.py`
callers:  `reports/views.py:report_detail` (writes a row after each export)
door:     two-way — a table in the existing store, a normal migration undoes it
proof:    export a report twice, then read `export_history` back and see two rows with the right timestamps
effort:   S
after:    1
