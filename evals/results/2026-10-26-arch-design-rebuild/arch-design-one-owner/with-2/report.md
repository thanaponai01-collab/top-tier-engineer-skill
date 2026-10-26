I ran the audit and its check passed on all three stages: read, move, and nothing changed. I read every file in `fixture/` (7 files, 45 lines). The repo has no architecture doc, so a newcomer has nothing written down to go on.

**Overall:** messy in places. Nothing is tangled, but there's one trap a newcomer could easily fall into.

## What they should know before changing anything

**1. Never touch `billing/invoice.py::invoice_date` when "cleaning up" date formatting.**
- The customer-facing date format (`%d/%m/%Y`) is written out three times, under three different names:
  - `api/serializers.py:1` as `format_date`
  - `jobs/export.py:1` as `date_str`
  - `web/views.py:1` as `fmt_date`
- A fourth function, `billing/invoice.py:1`, looks like another copy, but it isn't. The tax authority's upload spec requires ISO-8601 (`%Y-%m-%d`), and if that field changes the whole filing is rejected. The only warning is a comment.
- Searching for `strftime` turns up all four, so a "dedupe the date helpers" change will very likely pull billing in.
- I ran all four in a temp copy: the three display ones give `04/03/2026` and invoice gives `2026-03-04`.
- **Cost today:** changing the display format means editing 3 files. Miss one and the CSV export or the web page stops matching the API.

**2. The `providers/` plug-in setup is mostly unused.**
- There's a base class, a registry and one SMTP implementation (`providers/base.py:1`, `providers/registry.py:3`, `providers/smtp.py:4`), and nothing outside `providers/` uses any of it.
- It costs some reading time, not change time: adding a new channel means touching 2 files.
- Treat it as a stub. Don't build on top of it or delete it without a reason.

## Recommended move (two-way door: easy to undo)

**Put the three display-date copies into one function and keep billing out of it on purpose.**
1. Create a `display_date(d)` function in a new `dates.py`, moved from `api/serializers.py:1`.
2. Change the callers at `api/serializers.py:6`, `jobs/export.py:6` and `web/views.py:6` to use it, and delete the three local copies.
3. Leave `billing/invoice.py` alone. Add a comment in `dates.py` saying the tax filing format lives in billing and must never import from here.

**Proof:** this command passes today in a throwaway copy. Rerun it from `fixture/` after each step:
```
python -B -c "import datetime as t;from api.serializers import order_json;from jobs.export import rows;from web.views import order_page;from billing.invoice import line;o={'id':7,'placed_at':t.date(2026,3,4)};assert order_json(o)['placed_at']=='04/03/2026';assert rows([o])==['7,04/03/2026'];assert order_page(o)=='Order 7 placed 04/03/2026';assert line(o)=='7|2026-03-04';print('ok')"
```
The last assert is the important one: it fails if billing's date format ever changes.

**What I'm not recommending:**
- **One shared date function for all four, billing included.** If that were done, the next display-format change would silently change the tax filing.
- **Deleting the provider setup.** It saves two small files, but the next channel (SMS, for example) would bring it back.

**Seen in passing (not a structural issue):** `providers/registry.get()` raises a bare `KeyError` when given an unknown provider name. Nothing calls it today.

Nothing in `fixture/` was changed; the probes ran in a temp copy, which I've deleted. Which do you want to explore: the date move, or the provider setup?