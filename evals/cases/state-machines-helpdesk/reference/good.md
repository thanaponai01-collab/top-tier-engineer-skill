# State machines in desk

Ticket state (new, open, pending, solved, closed, escalated), agent presence (online, away, offline), the CRM sync flags, article status, webhook delivery status and agent roles.

## Bugs, fixed
- **Auto-assign never assigns anything.** `routing/assign.py` keeps agents whose presence is `"available"`, but nothing sets that; presence is online, away or offline. Now it looks for `online`.
- **The SLA report always says 0 solved.** It counts `state == "resolved"`; tickets become `solved`. Fixed.
- **A reply reopens closed tickets.** `inbound/email.handle_reply` sets any ticket open. The README says closed is final, so a reply to a closed ticket now starts a new ticket with `parent_id` pointing at the old one.
- **One rate limit stops the CRM sync for good.** On `RateLimited`, `CrmSync.run` returns with `syncing` still true, so every later run says busy. It now clears `syncing`.
- **Escalated is a dead end.** `take()` only accepts new or open tickets, so nothing leaves escalated. A senior agent can now take escalated tickets.

Each has a test that failed before the fix.

## Looked odd, left alone
- The SLA report skips `channel == "fax"`. No code in desk writes "fax" as a literal, but the partner API sets the channel from its payload, and the README says fax tickets come that way.
- `notify_desktop` / `notify_mobile` are independent; every mix is fine.
- `reopen` is guarded by `@from_states("solved")`.
