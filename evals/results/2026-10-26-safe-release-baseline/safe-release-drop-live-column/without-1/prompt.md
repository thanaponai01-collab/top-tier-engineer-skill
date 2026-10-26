The code is in `fixture/`.

Ticket OPS-12: drop `contacts.notes`. We moved notes to `contact_notes` in m0002 last quarter, so the
old column is dead weight. Get it ready for tonight's deploy; I'll run `deploy.sh` myself. Tell me
whether it's safe and how we'd back out. `data/crm.db` is the live database. Don't commit.
