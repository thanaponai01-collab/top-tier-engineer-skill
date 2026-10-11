This is a small Python billing library for invoicing, about 70 lines of source with no dependencies and no persistence. I've put what I learned into notes in `fixture/`. `python -m unittest` passes (3 tests).

**How it works**
- `api.py` has three entry points: `create`, `send` and `correct`.
- `billing/invoices.py` creates, edits and sends invoices, and `billing/credit_notes.py` issues credit notes.
- `billing/notify.py` handles customer emails; it only appends to an in-memory `OUTBOX`.
- `store.py` holds the in-memory dicts.
- The two rules in `BRIEF.md` are enforced in code:
  - A sent invoice can't be edited, so corrections are credit notes (the accountant's audit requirement, 2026-08-12).
  - Each invoice is emailed once, because `send` returns False on a repeat.
- `BUILD.md` says the next step is partial credit notes.

**Prediction check**
I predicted from the notes that crediting an unsent invoice raises `ValueError`, and it did.

**Gap I found**
Nothing stops you crediting the same invoice twice. Two calls on a 20 invoice gave a total credit of −40. This matters for the partial credit notes work.

**Notes I changed**
- I rewrote `docs/architecture.md`. It was stale: it pointed at `billing/mailer.py` (renamed to `notify.py` on 2026-09-02) and left out credit notes.
- I added `docs/commands.md`, `FEATURES.md` and `VERIFY.md`. `FEATURES.md` maps each feature to its entry point and check. `VERIFY.md` lists what the tests don't cover.
- I extended the start-here block in `CLAUDE.md` to link all of these and flag the double-credit gap.
- I kept `BRIEF.md` and `BUILD.md` unchanged.

**Limits**
- I skipped the `foundation.py` snapshot and the memory index. I also didn't run a mutation challenge on the tests.
- The tests don't cover rejecting an unsent invoice, the credit-note email, or duplicate credits.
- I don't know why the repo is built this way beyond what's in `BRIEF.md`; there's no git history here.

**Next:** decide how duplicate and partial credits should behave, then add a guard and a test before building partial credit notes.

<!-- file written by the agent: fixture/FEATURES.md -->
# Features (complete map; the repo is tiny)

| Feature | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Create invoice | BRIEF | `api.create` | `invoices.create` | used by all tests | proven |
| Send once, email once | BRIEF invariant 2 | `api.send` | `invoices.send`, `notify.invoice_sent` | `test_send_once` | proven |
| Sent invoice immutable | BRIEF invariant 1 | `invoices.edit` (no api wrapper) | `invoices.edit` | `test_sent_invoice_immutable` | proven |
| Correct via credit note | BRIEF decision 2026-08-12 | `api.correct` | `credit_notes.issue` | `test_credit_note` | proven; unsent rejection run by hand, not in tests |
| Partial credit notes | BUILD.md Next | none | not built | none | unbuilt |

Untested: credit-note email in OUTBOX, double-credit guard (absent), unsent rejection.


<!-- file written by the agent: fixture/VERIFY.md -->
# Verify

- Command: `python -m unittest` from the repo root. Expect `OK`, 3 tests.
- Covers: invoice send-once, sent-immutability, whole-invoice credit note leaving the original total unchanged.
- Blind spots: unsent-invoice credit rejection, credit-note email, duplicate credits, anything persistent (no storage).
- Last run: green 2026-10-11. No mutation challenge has been done.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

Run from the repo root (no dependencies, no config).

| Command | Purpose | Status |
|---|---|---|
| `python -m unittest` | all tests (`tests/test_billing.py`, 3 tests) | observed green 2026-10-11 |
