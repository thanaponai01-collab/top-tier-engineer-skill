**Verdict: clean, with one trap.** I chose **Improve**. There is nothing to replace, and the fixture is 7 files and about 40 lines. The one thing a new person must know is that the three date helpers that look like duplicates are not all the same kind of thing.

## What to know before changing things

**1. Don't "dedupe the date helpers" into one function.**
- `%d/%m/%Y` is written out 3 times: `web/views.py:2`, `api/serializers.py:2` and `jobs/export.py:2`. A tidy-up pass will want to merge them.
- `billing/invoice.py:5` uses `%Y-%m-%d`. Its comment (`invoice.py:2-4`) says the tax authority's upload spec fixes this format, and that changing it rejects the whole filing.
- Pointing `invoice_date` at a shared helper would break that. A shared helper is the thing someone would later change when the customer-facing format changes.
- **Same-reason test:**
  - `invoice_date` changes only when the tax authority's spec changes. Keep it separate, and keep its comment.
  - `views.py` is the customer-facing display, so it changes with the UI.
  - `serializers.py` is an API contract with clients, and `export.py` is a file other people read. Either could be pinned by something I can't see from the code.
  - So I'd merge nothing without knowing who consumes the API and the export. Merging `views.py` into one shared display helper is the only plausible candidate, and it saves one 2-line function. That makes it tidying, not a move.
- **Proof if you do touch dates:** add a test that `invoice_date(date(2026,1,2)) == "2026-01-02"` before any date refactor. The fixture has no tests, so nothing guards it today.

**2. The `providers/` layer is speculative structure, but I can't prove it's safe to remove.**
- `base.py:2` says it's "implemented once, by SmtpProvider". `registry.py:3` is a one-entry dict, so there are 3 files for 1 implementer.
- Nothing inside `fixture/` calls `providers.registry.get`. I only searched `fixture/`, so I'd call it **suspected** dead, not proven.
- There is no git history in this directory to say why the layer exists. That reason may be a planned second provider, so don't delete it on sight.
- If you want to simplify it, the second option is to inline `SmtpProvider` and drop `base.py` and `registry.py`. That is a two-way door. Do it only after checking the real callers and the history.

## What to do first
1. Add the `invoice_date` format test (about 5 lines). It's the only change that protects against the expensive failure.
2. Leave the `%d/%m/%Y` copies alone unless you learn they truly share one owner.
3. Before touching `providers/`, find its callers and ask whoever added it.

## Limits of this audit
- The fixture has no tests, no git history and no entry points, so I traced only what is in these 7 files.
- Every claim above is **traced** from reading the files, except the dead-code question, which is **suspected**.
- No MCP servers were used. Several need authorization before they work, and none were needed here.