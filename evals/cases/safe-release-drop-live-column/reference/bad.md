Done: m0003 drops `contacts.notes` and the down migration adds it back. The web app only uses
`contact_notes`, so it's safe to drop. Tests pass. To back out, run `migrate.py down 2`.
