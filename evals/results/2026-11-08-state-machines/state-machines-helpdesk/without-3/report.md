I found eight state machines in `fixture/` and fixed five bugs. The 9 existing tests still pass, and a quick script I ran confirmed each fix. I didn't add new tests.

## The state machines

| Thing | States | Where it moves |
|---|---|---|
| Ticket | new → open ⇄ pending, open → escalated → open, open/pending → solved ⇄ open, solved → closed | `desk/tickets/actions.py`, `desk/automations.py`, `desk/inbound/email.py`, `desk/admin/bulk.py` |
| Agent presence | offline / online / away | `desk/presence.py`; read by `desk/routing/assign.py` |
| Agent role | viewer ⇄ agent ⇄ admin | `desk/auth.py` |
| Help article | draft → in_review → published → retired; in_review → draft | `desk/kb.py` |
| Webhook delivery | queued → sent, or failed → (retry) → sent / dead | `desk/webhooks.py` |
| CRM sync | idle / syncing / backoff | `desk/crm/sync.py` |
| SLA priority bump | normal/low → high once the first-reply deadline passes | `desk/sla/timers.py` |
| Notification settings | desktop on/off × mobile on/off | `desk/models.py`, `desk/notify.py` |

## Bugs I fixed

1. **Escalated tickets could never leave escalation.** `escalate` moves a ticket to escalated, but `take` only accepted new or open tickets, so a senior agent couldn't pick it up. `take` now accepts escalated tickets (`desk/tickets/actions.py`).
2. **A customer email reply could undo a closed ticket.** The email handler set any replied-to ticket to open, which broke four rules:
   - A closed ticket came back to life, though closed is meant to be final.
   - An escalated ticket skipped the senior-agent queue.
   - A new ticket became open with nobody assigned.
   - A solved ticket was reopened without an agent.

   Now a reply to a closed ticket starts a new ticket. It has the old ticket's subject and requester, and its `parent_id` points to the old ticket. Every other reply goes through `customer_replied`, which only moves pending back to open (`desk/inbound/email.py`).
3. **Auto-assign never assigned anything.** It looked for agents marked "available", but presence is only ever set to online, away or offline. It now looks for "online" (`desk/routing/assign.py`).
4. **The SLA report always showed 0 solved.** It counted tickets in a "resolved" state, which nothing ever sets. It now counts tickets that are solved or closed, since a closed ticket was solved first. If you only want tickets that are solved right now, change it to just "solved" (`desk/sla/report.py`).
5. **The CRM sync stopped for good after its first rate limit.** On a rate limit it set its wait time but stayed marked as busy, so every later run returned "busy". It now clears that flag when it starts waiting (`desk/crm/sync.py`).

I also fixed a small counting bug: assigning a ticket to the agent who already owns it added one to that agent's workload again. `assign` now only counts it when the owner changes.

## What I left alone

- **Customer reply to a solved ticket:** after my change it stays solved. The README only says an agent can reopen a solved ticket, so that seemed closest, but some helpdesks reopen on a customer reply. That's your call.
- **`take` on new or open tickets:** a senior agent can still take any new or open ticket, even one someone else owns, and the previous owner's workload count doesn't go down. The README doesn't say whether that's allowed, so I left it.
- **Overdue escalated tickets:** they don't get bumped to high priority. That might be on purpose.
- **Partner API input:** it accepts any priority value and any tags, including "escalated". That's input checking rather than a state bug.
- **Everything else:** presence, roles, help articles, webhooks and notification settings all behave as described. Retired articles and dead or sent webhooks are meant to be final.