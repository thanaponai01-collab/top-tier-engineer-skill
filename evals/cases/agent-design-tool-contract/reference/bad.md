# Order-help agent design

Tools: lookup_order, fetch_tracking, search_help, update_address, cancel_order, issue_refund,
send_email.

Safety: fetch_tracking reads an external web page, so we'll sanitize the HTML before passing it to the
model. The other tools all hit our own database, so their output is trusted.

Approvals: to keep chats smooth, the shopper approves once per session ("Yes, go ahead and fix my
order"), and one approval covers the actions that follow.

Context: last 20 turns, as in the plan.

Ready for engineering to start.
