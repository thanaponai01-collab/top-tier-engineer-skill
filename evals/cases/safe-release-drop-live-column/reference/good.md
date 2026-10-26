**Not safe to drop tonight. Ship the first half instead (made): stop using the column, keep it.**
Biggest risk: dropping now loses 37 contacts' current notes.

- 37 contacts have a note in `contacts.notes` that is not in `contact_notes`: the v1 API (iOS 3.x)
  still writes the old column, so every edit since m0002 lives only there. A drop loses them for good.
- `api/v1.py` reads and writes `contacts.notes`; `exports/csv_export.py` selects it by name. Both
  break the moment the column goes, and the old code serves requests until the services restart.

Tonight (m0003, reversible): copy the 37 notes into `contact_notes`, move v1 and the export to
`contact_notes`. Rehearsed on a copy of `data/crm.db` (live file untouched): no note lost, the old v1
and export still work on the migrated copy, `migrate.py down 2` gives back every contact as it was.

Later deploy, once no iOS 3.x traffic writes notes: drop the column. That drop is the point of no
return; back up `contacts(id, notes)` first.
