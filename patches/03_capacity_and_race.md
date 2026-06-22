# Patch 03 — Atomic capacity check (resolves F3 overbooking + F4 race)

**Cause:** guard ignores requested seats (F3) AND reads occupancy before writing, unlocked (F4).
**Principle:** a shared-resource check and claim must be one atomic operation on the post-condition.

## Fix — correct arithmetic + atomic booking

`app/controller/tickets.py` — make booking atomic and post-condition-correct:
```python
from sqlalchemy import func

def createTicketChecked(data, capacity):
    """Book only if occupied + requested <= capacity, atomically."""
    requested = int(data['admits'])
    if requested <= 0:
        raise Exception('Seats must be positive')
    try:
        # lock the show's ticket rows for this transaction
        occupied = (db.session.query(func.coalesce(func.sum(Ticket.admits), 0))
                    .filter(Ticket.show_id == data['show_id'])
                    .with_for_update()        # SELECT ... FOR UPDATE (Postgres/MySQL)
                    .scalar())
        if occupied + requested > capacity:
            raise Exception('Not enough seats remaining')
        data['bookingTime'] = time_ns()
        data['code'] = sha256(f'{time_ns()}_{data["uid"]}'.encode()).hexdigest()[:8]
        t = Ticket(uid=data['uid'], show_id=data['show_id'], code=data['code'],
                   admits=requested, bookingTime=data['bookingTime'])
        db.session.add(t)
        db.session.commit()
        return t
    except Exception:
        db.session.rollback()
        raise
```

`app/views/ticket.py` — the POST branch passes capacity and drops the stale pre-read guard:
```python
def post():
    try:
        d = request.form
        if not d['seats'].isnumeric():
            raise Exception('Number of seats field is not a number')
        ticket = createTicketChecked(
            {'uid': detokenize(auth)['id'], 'show_id': id, 'admits': d['seats']},
            capacity=venue.capacity)
    except Exception as e:
        return render_template('show_booking.html', show=show, event=event, venue=venue,
                               occupied_seats=occupied_seats, error=str(e))
    return redirect(url_for('booking_confirmed', code=ticket.code))
```

**SQLite caveat (trace-only):** `with_for_update()` is a no-op on SQLite, whose concurrency is
whole-file locking; under SQLite the serial write order plus the in-transaction recount still
closes the common case, but true row-level locking requires Postgres/MySQL. Record this as a
`DECISION_LEDGER.md` entry: "booking integrity assumes a DB with row locks for production." This is
an arch-design force, surfaced not smuggled.

**Pre-verify:** the exact two proofs from LIVE_RUN_001 — request 5 into capacity 2 must now be
rejected; two concurrent bookings of (2,1) into capacity 2 must leave exactly one winner.
