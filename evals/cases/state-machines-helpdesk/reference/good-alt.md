Machines: ticket lifecycle, agent presence, CRM sync (syncing / last_error / backoff), KB article, webhook delivery, role.

Five bugs, all fixed with a test each:
1. eligible() filters presence == "available", which is never set anywhere (go_online sets "online"), so auto_assign hands out nothing.
2. report.counts uses "resolved" but solve() writes "solved", so solved is always zero.
3. handle_reply puts every ticket back to open, including closed ones. Closed is final per the README; a reply now creates a new ticket linked by parent_id.
4. After RateLimited the syncing flag stays true, so CrmSync is stuck on "busy" forever. Cleared it in that branch.
5. escalated has no way out: take() only accepts new/open. Added escalated to what take() accepts.

Not bugs: the fax filter (channel comes from the partner API payload), the desktop/mobile notification flags (independent, any mix valid), reopen (guarded by the from_states decorator).
