**What it is:** invoicing for small businesses. `api.py` creates, sends and corrects invoices.
Sent invoices are **immutable**: a correction is a credit note (BRIEF.md invariant 1, the
accountant's audit requirement).

**Main path:** `api.send` → `billing/invoices.py:send` sets `sent` and calls
`billing/notify.py:invoice_sent`, which queues one email (sending twice returns False). `api.correct` →
`billing/credit_notes.py:issue` refuses unsent invoices, records a negative note and emails it.

**Reused:** CLAUDE.md start-here, BRIEF.md, BUILD.md (kept as they are).
**Refreshed:** `docs/architecture.md` was **stale**. It still named `billing/mailer.py`, which was renamed
to `billing/notify.py` on 2026-09-02, and it had no `credit_notes.py` or `correct` path. Redrawn from the
imports, with `file:line` evidence.

**Prediction checked:** from the notes, crediting a sent invoice leaves its total unchanged. That
held: `python -m unittest` → 3 tests OK, including `test_credit_note` [proven].

Not read: nothing beyond these files (the repo is small). Next (BUILD.md): partial credit notes.
