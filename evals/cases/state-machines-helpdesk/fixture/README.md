# desk

A small helpdesk: customers write in by email, the web form or the partner API, agents answer, and
the support lead gets a weekly SLA report.

## How tickets move

- A ticket starts **new**. Assigning it (by hand or by auto-assign) makes it **open**.
- An agent can set an open ticket to **pending** while waiting on the customer; the customer's
  reply makes it open again. Pending tickets with no reply for 7 days are solved automatically.
- **Solved** tickets can be reopened by an agent. After 4 days solved they **close**.
- **Closed is final.** A customer reply to a closed ticket starts a new ticket, linked to the old
  one by `parent_id`, with the same subject and requester.
- An open ticket can be **escalated**. Escalated tickets wait for a senior agent to `take` them,
  which makes them open and assigned to that senior agent.

## Other rules

- Auto-assign gives new tickets to the least-loaded agent who is online right now. Agents who are
  away or offline, and viewers, never get tickets.
- Fax tickets come in through the partner API from the fax gateway; they are left out of the SLA
  report because their clock starts when the gateway types them in.
- Agents choose desktop and mobile notifications separately; any mix is fine.
- The CRM sync runs every minute. When the CRM rate-limits it, it waits as long as the CRM says and
  then carries on.

    python -m desk report
    python -m desk hourly
    python -m unittest discover tests
