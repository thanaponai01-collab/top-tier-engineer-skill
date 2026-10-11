Here's the picture, and what I fixed so the next session starts right.

The system: api.py is the front door for create, send and correct. invoices.py owns the invoice
lifecycle. Once sent, an invoice can't be edited (edit raises AlreadySent), which is the owner's rule
in BRIEF.md: fixes go through credit notes. credit_notes.py issues those, and notify.py sends the
customer emails.

The architecture doc that CLAUDE.md points every session at was out of date. It described
billing/mailer.py, a module that no longer exists (notify.py replaced it in September), and it left
credit notes out entirely. I rewrote docs/architecture.md from the actual imports. I left BRIEF.md,
BUILD.md and the code alone.

To check I understood it, I predicted that a credit note leaves the original invoice's total untouched
and ran the tests (3 passed). The next piece of work, per BUILD.md, is partial credit notes.
