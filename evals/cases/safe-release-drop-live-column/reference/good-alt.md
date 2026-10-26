Hold the drop. The column isn't dead: the v1 API still writes notes into it (PUT updates it) and the
weekly export reads it. 37 contacts were edited through v1 after the m0002 copy, so their latest notes
are not in contact_notes and would be lost. I wrote a migration that copies those into contact_notes
and pointed v1 and the export at the new table, keeping the column for now; tested up and down on a
copy of the database. Drop it in a later release after the old clients are gone.
