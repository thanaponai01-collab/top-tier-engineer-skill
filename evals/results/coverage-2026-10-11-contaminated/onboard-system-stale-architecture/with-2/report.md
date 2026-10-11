**Summary:** `fixture/` is a small in-memory invoicing library in Python with no dependencies. It lets you create an invoice, send it once, and correct it with a credit note. `python -m unittest` passes, 3 tests (proven). I read every file, so nothing was left unread. The repo isn't under git, so there's no history to check.

**Flow (traced):**
- **Entry points:** `api.py` has three functions: `create`, `send` and `correct`.
- **Invoices:** `billing/invoices.py` creates, edits and sends invoices. `send` flips `sent` to true before it notifies, so a repeat call returns False and sends nothing. That is how "emailed exactly once" is held.
- **Credit notes:** `billing/credit_notes.py` makes a negative-amount note for the full invoice total, and only for a sent invoice. This is the "corrections are credit notes, not edits" decision from `BRIEF.md`. The only guard on editing a sent invoice is the `sent` check in `invoices.edit`.
- **Email and storage:** `billing/notify.py` just appends to `store.OUTBOX`, so no real email goes out. `store.py` holds module-level dicts, so everything is lost on restart.

**Prediction check:** From the notes I predicted that correcting a sent 20-unit invoice would give a -20 note and leave the invoice total at 20. That matches `test_credit_note` (proven).

**Finding (proven):** Calling `api.correct` twice on the same invoice creates two full-total credit notes, summing to -40 on a 20 invoice. `BRIEF.md` doesn't say whether that's allowed, so ask the owner before changing it. It matters for the planned partial credit notes.

**Repo changes:**
- **Refreshed:** `docs/architecture.md` was stale. It named `billing/mailer.py`, which was renamed to `notify.py` on 2026-09-02, and it left out credit notes. I rewrote it from the source. It now has a corrected diagram, a feature-to-entry-to-check table, how each invariant is held, the known gaps, and the check command.
- **Edited:** `CLAUDE.md` now points to the features table and the open question, and notes that there's no git history.
- **Kept as is:** `BRIEF.md` and `BUILD.md` were accurate. I didn't create `WHY.md` or `VERIFY.md`, because there's no further rationale to record and the one check command is already in `CLAUDE.md`.

**Not done:** The Drive plugin's foundation inventory and worker agents weren't run. The repo is small enough that I did the inventory directly.

**Next:** Settle the duplicate credit-note rule with the owner, then start partial credit notes from `BUILD.md`.