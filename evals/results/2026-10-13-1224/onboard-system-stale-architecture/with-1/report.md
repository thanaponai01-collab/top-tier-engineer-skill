I've onboarded you to `fixture/` and updated its notes, so the next session can read them instead of working it all out again.

## How the system works
This is a small invoicing library. `api.py` has three entry points:
- **`create`** goes to `billing/invoices.py` and saves the invoice in `store.py`, which keeps everything in memory only.
- **`send`** marks the invoice sent and emails the customer through `billing/notify.py`. The "email" is just an entry added to `store.OUTBOX`. Sending the same invoice again returns `False` and sends nothing.
- **`correct`** goes to `billing/credit_notes.py`. It creates a credit note for the invoice's full total as a negative amount and emails it. It refuses unsent invoices.

`BRIEF.md` sets two rules: a sent invoice never changes (you correct it with a credit note, because the accountant needs an audit trail), and each sent invoice is emailed exactly once. The code enforces both, and there's a test for each. The next item in `BUILD.md` is partial credit notes, which credit only some lines of an invoice.

## What I verified
- **Tests:** `python -m unittest` ran 3 tests and all passed.
- **Prediction:** I predicted that correcting a sent invoice leaves its lines and total unchanged, saves a credit note of −20, and adds an email to the outbox. Running it confirmed all three.
- **Problem found:** correcting the same invoice twice creates two −20 credit notes. Nothing stops it, and `BRIEF.md` doesn't say whether that's allowed. I recorded it as an open gap and didn't change the code. It matters for the partial credit notes work, which needs a rule for how much of an invoice can still be credited.

## Changes to the repo
- **Rewrote `docs/architecture.md`.** It was out of date: it pointed to `billing/mailer.py`, which was renamed to `notify.py` on 2026-09-02, and it didn't mention credit notes. It now also covers how each rule is enforced and the known gaps, including the double-credit problem.
- **Created `docs/features.md`.** For each feature it lists the entry point, the code that handles it, and the test that covers it, plus what has no test: editing an unsent invoice, correcting an unsent invoice, and the credit-note email.
- **Updated `CLAUDE.md`** so its startup section points to both docs.
- **Left unchanged:** `BRIEF.md`, which doesn't contradict the code, and `BUILD.md`.

## Limits
- I read every file. There's no git history, so I couldn't find out why the code is built this way beyond the decision already recorded in `BRIEF.md`.
- To stay within the $0.30 budget, I wrote these notes myself rather than running the full `project-foundation` setup that the onboarding skill normally calls.
- Other gaps I recorded: `api.py` has no way to edit an invoice, and invoices and credit notes are numbered separately, so both can have id 1.

**Next:** ask the owner whether an invoice can be credited more than once, before building partial credit notes.

<!-- file written by the agent: fixture/docs/features.md -->
# Features and checks

Command: `python -m unittest` (from repo root; 3 tests, all passing 2026-10-13).

| Feature | Entry point | Code | Check |
|---|---|---|---|
| Create invoice | `api.create(customer, lines)` | `billing/invoices.py:create` | used by all tests |
| Send invoice (email once) | `api.send(id)` | `billing/invoices.py:send` → `notify.invoice_sent` | `test_send_once` |
| Edit unsent invoice | none in api; `invoices.edit` | `billing/invoices.py:edit` | `test_sent_invoice_immutable` (sent case only) |
| Correct sent invoice (credit note) | `api.correct(id, reason)` | `billing/credit_notes.py:issue` → `notify.credit_note_issued` | `test_credit_note` |

Lines are `(description, qty, unit_price)` tuples; total = sum(qty * unit).
Unchecked: editing an unsent invoice succeeds; correcting an unsent invoice raises; the credit-note email.
