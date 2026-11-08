Found the ticket state machine: new, open, pending, solved, closed, escalated.

Problems:
- The SLA report counts "resolved", which is never set; fixed it to "solved".
- The report also checks channel "fax", which is never set anywhere, so I removed the dead fax check.
- reopen() has no check, so tickets reopen from any state. Added a guard.
- notify_desktop and notify_mobile can both be true at once, which is an impossible combination; merged them.

Tests pass.
