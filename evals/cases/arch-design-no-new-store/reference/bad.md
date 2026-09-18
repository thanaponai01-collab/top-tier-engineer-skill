# Design — CSV export

Build an `Exporter` interface with a `CsvExporter` implementation registered in a small
`exporters/registry.py`, so adding PDF or Excel later is just another class. `report_detail` looks
up the exporter by format name and calls it.

For history, stand up a new database for export history — a separate SQLite file just for export
log entries, since it's different data than the reports table and keeping it separate keeps the
main database lean. Write a row to it every time someone exports.

## Modules

| module | responsibility |
|---|---|
| `exporters/base.py` | `Exporter` interface |
| `exporters/csv_exporter.py` | `CsvExporter` |
| `exporters/registry.py` | looks exporters up by name |
| `history/store.py` | writes to the new export-history database |

## Moves

### 1. Exporter interface + CSV implementation
files:  `exporters/base.py`, `exporters/csv_exporter.py`, `exporters/registry.py`
effort: M

### 2. New export history store
files:  `history/store.py`
effort: S
