This is a small Python invoicing app (create, send and correct invoices). It has no dependencies, and `python -m unittest` passes all 3 tests.

**What it's for.** `BRIEF.md` sets two rules:
- A sent invoice never changes. Corrections are credit notes that reference it, which is what the accountant's audit requires (decision of 2026-08-12).
- Each sent invoice is emailed to the customer exactly once.

**How it's laid out**
- `api.py` is a thin layer with `create`, `send` and `correct`.
- `billing/invoices.py` handles create, edit, total and send. `send` is idempotent, and `edit` raises `AlreadySent` on a sent invoice.
- `billing/credit_notes.py` issues a full-amount negative note for a sent invoice and emails it.
- `billing/notify.py` holds the customer emails. "Sending" just appends to `store.OUTBOX`.
- `store.py` keeps everything in memory, so nothing is persisted.

**Where the work stands.** Credit notes were built on 2026-09-20. The next step in `BUILD.md` is partial credit notes (credit some lines, not the whole invoice).

**What I found**
- `docs/architecture.md` was stale. It still referenced `billing/mailer.py`, which was renamed to `notify.py` on 2026-09-02, and it left out credit notes. I rewrote it with the current diagram, data shapes and a "Known gaps" section.
- The same sent invoice can be credited repeatedly, and no test covers that. Partial credit notes will need a rule that the notes on an invoice never add up to more than its total, so I flagged that in `BUILD.md`.
- Tests don't cover the credit-note email or the rejection of unsent invoices.
- Invoice ids and credit-note ids come from separate counters, so they can be the same number.

I changed only `docs/architecture.md` and `BUILD.md`, and left the code alone. `CLAUDE.md` already points the next session to `BRIEF.md`, `BUILD.md` and the architecture doc, so it didn't need changes.