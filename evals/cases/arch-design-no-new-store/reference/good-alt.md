# CSV export — structure before code

Two things to decide here, and only one of them is expensive to get wrong.

**Storage for export history:** put it in the database this app already has. `app/db.py` is the
single place `reports/models.py` and `users/models.py` both go through for persistence — a new
table there is a normal, reversible migration. Standing up a dedicated store just for a timestamp
and a title is not: once it holds real history, walking it back means a migration off a whole
system, not a column drop, plus a second thing this team has to secure and back up. Do not give
export history its own datastore — the existing database already owns this job.

**Producing the CSV:** stdlib's `csv` module, called from one new function. One format is on the
table, so an exporter interface or a registry of formats would be paying for a second
implementation that doesn't exist yet. That seam earns its place the day a second format shows up,
not before.

| module | responsibility | owns |
|---|---|---|
| `reports/export.py` | build the CSV bytes for one report | column order, formatting |
| `app/db.py` | reads and writes everything persisted | + the `export_history` rows |

`report_detail` in `reports/views.py` calls `export.py` and then writes a history row through
`app/db.py` — no new module talks to storage directly.

## Moves

Context: no new datastore, no new service; `app/db.py` keeps being the only thing that touches
storage.

### 1. `reports/export.py`: one report to CSV
cost:     none — new work
files:    `reports/export.py` (new)
owner:    `reports/export.py`
callers:  `reports/views.py:report_detail`
door:     two-way — a pure function, replace it whenever
proof:    run it on a fixture report, diff the bytes against an expected CSV
effort:   S
after:    nothing

### 2. `export_history` table through `app/db.py`
cost:     none — new work
files:    `app/db.py`
owner:    `app/db.py`
callers:  `reports/views.py:report_detail`
door:     two-way — a table in the existing store, drop or rename it with a migration
proof:    export twice, read the table back, see two rows
effort:   S
after:    1
