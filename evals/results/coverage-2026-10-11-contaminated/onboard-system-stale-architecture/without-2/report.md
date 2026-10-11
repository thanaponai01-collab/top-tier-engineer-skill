`fixture/` is a small in-memory Python billing app for invoices and credit notes. I ran `python -m unittest` and all 3 tests pass.

**What it does**
- **Entry points:** `api.py` has `create`, `send` and `correct`.
- **Invoices:** `billing/invoices.py` creates, edits (unsent only) and sends invoices. `send` returns False if the invoice was already sent, so no second email goes out.
- **Credit notes:** `billing/credit_notes.py` issues a full-amount negative note against a sent invoice. It never touches the invoice itself.
- **Email:** `billing/notify.py` only appends to `store.OUTBOX`, so nothing is really emailed yet.
- **Storage:** `store.py` is plain in-memory dicts.

**Rules to keep** (from `BRIEF.md`)
- A sent invoice never changes. Corrections are credit notes only, because the accountant's audit requires it.
- Each sent invoice is emailed exactly once.

**Where the work is:** the next task is partial credit notes (credit some lines, not the whole invoice). It touches `credit_notes.issue` and `api.correct`.

**Gaps I found (code unchanged)**
- Nothing stops several full credit notes being issued against one invoice, so the total credited can exceed the invoice. This matters for the partial-credit work.
- No test covers crediting an unsent invoice, which raises `ValueError`.
- No test covers the credit-note emails.

**What I changed for the next session**
- `docs/architecture.md` was stale: it named `mailer.py` (renamed to `notify.py` on 2026-09-02) and left out credit notes. I redrew the diagram and module notes.
- `BUILD.md` now has a verified-state section with the test status, the gaps above, and what partial credit will touch.
- `CLAUDE.md` already pointed to the right files, so I left it alone.