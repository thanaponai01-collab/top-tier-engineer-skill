I found seven implicit state machines and fixed five bugs. All 16 tests pass: the 9 that were there before and 7 new ones I added for the fixes.

## The state machines

**1. Ticket** (`state`): new → open → pending / solved / escalated → closed. The moves happen in `desk/tickets/actions.py`, `desk/automations.py`, `desk/inbound/email.py` and `desk/admin/bulk.py`. They are read in `routing/assign.py`, `sla/report.py`, `sla/timers.py` and `crm/fields.py`.

**2. Agent presence** (`presence`): offline / online / away, changed in `desk/presence.py`. Auto-assign reads it.

**3. Agent role**: viewer ↔ agent ↔ admin, changed in `desk/auth.py` (promote/demote). No bugs.

**4. Knowledge-base article**: draft → in_review → published → retired, and in_review can go back to draft. This is in `desk/kb.py`. No bugs.

**5. Webhook delivery**: queued → sent / failed / dead, and failed can be retried. This is in `desk/webhooks.py`. No bugs.

**6. CRM sync**: idle / syncing / backing off, using the `syncing` and `backoff_until` fields in `desk/crm/sync.py`.

**7. Notification settings**: desktop and mobile are two separate on/off switches, so any mix works as the README says. No bugs.

## Bugs fixed

1. **Escalated tickets could never leave escalated** (`tickets/actions.py`, `take`). `take` only accepted *new* or *open* tickets, so a senior agent could not pick up an escalated one, and they could also "take" ordinary open tickets. Now `take` only accepts escalated tickets.
2. **Auto-assign never gave anyone a ticket** (`routing/assign.py`). It looked for agents whose presence is `"available"`, but nothing ever sets that. Presence is only `online`, `away` or `offline`, so I changed the check to `"online"`. Away, offline and viewer agents are still left out.
3. **The SLA report always said 0 solved** (`sla/report.py`). It counted tickets in a `"resolved"` state, which doesn't exist. It now counts *solved* and *closed* tickets, since a closed ticket was solved first.
4. **A customer email reply changed tickets it shouldn't have** (`inbound/email.py`). Any reply set the ticket straight to *open*, so:
   - A **closed** ticket came back to life, but closed is meant to be final. Now the reply starts a new ticket with the same subject and requester, linked to the old one by `parent_id`.
   - An **escalated** ticket went back to open without any senior agent taking it. It now stays escalated.
   - A **new** ticket became open with nobody assigned, which is a state that shouldn't exist. It now stays new, so auto-assign still picks it up.
   - A **pending** ticket going to open was already right and still works.
5. **CRM sync stopped for good after being rate-limited** (`crm/sync.py`). When the CRM rate-limited it, the "syncing" flag was never cleared, so after waiting it answered "busy" forever. The flag is now always cleared, including after errors.

## Left alone (worth knowing about)

- **Customer email reply to a *solved* ticket**: it still reopens the ticket, as before, and now also clears the solved time. The README only says an agent can reopen, so this might be wrong. But changing it would mean a customer's "still broken" email gets ignored and the ticket closes anyway, so it's your call.
- **`customer_replied` on a closed ticket** (`tickets/actions.py`) adds the comment to the closed ticket instead of starting a new one. It can't create a ticket because it has no access to the ticket store. I didn't change what it takes as input.
- **Agent load only ever goes up.** It increases on assign and take but never goes down on solve, close or reassignment. Assigning the same agent twice also counts twice. Over time every agent will hit the limit of 12 and auto-assign will stop. This is clearly a problem, but the README doesn't say what "load" should count, so I didn't guess.
- **`take` replaces the previous assignee** without taking that ticket off their load. This is the same load problem.
- **Unanswered escalated tickets don't get bumped to high priority**, because `bump_overdue` only looks at new and open tickets. That may be intended.