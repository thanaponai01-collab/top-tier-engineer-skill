# Patch 04 — Schema & lookup fixes (resolves F5 unique admits + F6 OR-filter)

## F5 — `Ticket.admits` must not be unique
`app/models/ticket.py`:
```python
admits = db.Column(db.Integer, nullable=False)   # was: unique=True
code   = db.Column(db.String, nullable=False, unique=True)  # identity is what's unique
```
**Migration (hands to data-evolution):** dropping a UNIQUE constraint and adding one on `code` is a
schema change on a populated table — expand/contract, not an in-place edit. See `data-evolution`.

## F6 — deliberate single-key lookups
`app/controller/tickets.py` — replace the OR-finder with explicit finders:
```python
def getTicketByCode(code):
    return db.session.query(Ticket).filter(Ticket.code == code).first()

def getTicketById(id):
    return db.session.query(Ticket).filter(Ticket.id == id).first()
```
Update callers (`views/ticket.py show_ticket` uses code → `getTicketByCode`).
Apply the same split to `getUser(uid, email)` in `controller/user.py`:
`getUserByEmail`, `getUserById`.

**Pre-verify:** `getTicketByCode('abc')` returns only the row whose code is 'abc' (or None);
the LIVE_RUN_001 collision (`getTicket(id=1)` returning an unrelated show) can no longer occur.
