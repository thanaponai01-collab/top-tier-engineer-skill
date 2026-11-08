I found eight state machines in the app and fixed five bugs in them. The 9 existing tests still pass. I also ran a scripted walk-through of every fixed path, and each one now behaves as the README describes. I didn't add any new test cases to the test suite.

## The state machines

| Thing | States | Where it moves |
|---|---|---|
| Ticket | new → open ⇄ pending, open → escalated → open, open/pending → solved → open (reopen) / closed | `desk/tickets/actions.py`, `desk/inbound/email.py`, `desk/automations.py`, `desk/admin/bulk.py` |
| Agent presence | offline / online / away | `desk/presence.py`, read by `desk/routing/assign.py` |
| Agent role | viewer ⇄ agent ⇄ admin | `desk/auth.py` |
| CRM sync | idle / busy / backoff / error | `desk/crm/sync.py` |
| Webhook delivery | queued → failed (retries) → sent / dead | `desk/webhooks.py` |
| Knowledge-base article | draft ⇄ in_review → published → retired | `desk/kb.py` |
| SLA priority bump | any → high when overdue | `desk/sla/timers.py` |
| Notification settings | desktop and mobile each on or off | `desk/models.py`, `desk/notify.py` |

## Bugs I fixed

1. **A customer email could reopen a closed ticket** (`desk/inbound/email.py`). Any reply set the ticket to `open`, whatever state it was in. That broke four things:
   - "Closed is final" didn't hold.
   - An escalated ticket could become open without a senior agent taking it.
   - A brand-new ticket could become open with nobody assigned. Auto-assign only looks at `new` tickets, so it would then never pick it up.
   - A solved ticket could be reopened by the customer, but the README says only an agent can do that.

   **Fix:** a reply to a closed ticket now starts a new ticket with the same subject and requester, linked by `parent_id`. Any other reply goes through the normal "customer replied" step, which only moves pending to open.

2. **Escalated tickets were stuck forever** (`take` in `desk/tickets/actions.py`). `take` refused tickets in the `escalated` state, and nothing else moves a ticket out of it. **Fix:** `take` now accepts escalated tickets.

3. **Auto-assign checked for a presence nothing sets** (`desk/routing/assign.py`). It only picked agents who were `"available"`, but presence is only ever `online`, `away` or `offline`, so no ticket was ever auto-assigned. **Fix:** it now checks for `"online"`.

4. **The SLA report checked for a state nothing sets** (`desk/sla/report.py`). It counted tickets that were `"resolved"`, which is never set, so "solved" in the report was always 0. **Fix:** it now counts `solved` and `closed`. I included closed because those tickets were solved first and close on their own after 4 days. Change that if the report should only count tickets that are currently solved.

5. **The CRM sync got stuck after being rate-limited** (`desk/crm/sync.py`). When the CRM rate-limited it, the sync kept its "busy" flag. After the wait it said "busy" forever and never ran again. **Fix:** it clears the flag on that path too.

## Left alone (worth a look, but I wasn't sure enough to change them)

- **`take` still accepts new and open tickets**, as before. That means a senior agent can take a ticket away from whoever has it. The README only mentions taking escalated tickets, but I didn't want to break callers who rely on this.
- **Workloads only go up.** When a ticket is taken from someone, their count isn't lowered. Assigning a ticket to the agent who already has it raises their count again. Solving or closing never lowers it. Over time agents look busier than they are and stop getting auto-assigned once their count reaches 12.
- **Nothing checks permissions on ticket actions.** `assign`, `solve` and the others never ask who is doing them. Auto-assign does keep viewers out.
- **Saved data isn't checked when loaded.** A ticket's state comes back from the saved file as-is, so a bad value is accepted.
- **Partner API priority isn't checked.** Tickets from the partner API can arrive with any priority value.
- **No problems found** in presence, roles, webhooks, knowledge-base articles or notifications. They match the README, or the README doesn't cover them. Retired articles and dead webhook deliveries can't move again, which looks deliberate.