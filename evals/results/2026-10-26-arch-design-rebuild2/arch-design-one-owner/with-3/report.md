I ran the arch-design audit on `fixture/` and it passed all three stages. I changed nothing in the repo; the checks ran in a throwaway copy.

**Overall: messy in places.** It's a small codebase (7 files, 45 lines), but a newcomer could trip over one thing in particular.

## What they should know before Monday

**1. The date that looks like a duplicate must stay different.** The customer-facing date format (`%d/%m/%Y`) is written out three times:
- `api/serializers.py:1` `format_date`
- `jobs/export.py:1` `date_str`
- `web/views.py:1` `fmt_date`

A fourth function, `billing/invoice.py:1` `invoice_date`, looks like a copy but isn't. It outputs ISO dates (`%Y-%m-%d`) because the tax authority's upload spec requires that format. The comment at `billing/invoice.py:2-4` says that changing it rejects the whole tax filing.

I confirmed this by running all four on 2026-03-04: the first three give `04/03/2026` and billing gives `2026-03-04`.

What this costs today: changing the display format means editing 3 files. Miss one and the API, the CSV export and the web page show different dates. "Tidying up" billing to match would break tax filing.

**2. `providers/` has a plugin seam with only one plugin.** `providers/base.py` defines `Provider`, `providers/smtp.py` is its only implementation, and `providers/registry.py:6` returns SMTP by default. They shouldn't build on the extension point as if it had been tested with other providers. Also, `get("unknown")` fails with a bare `KeyError` rather than a clear error.

**3. Imports assume you run from inside `fixture/`.** Imports like `from providers.smtp import ...` only resolve when `fixture/` is the working directory.

**4. There are no tests and no architecture doc.** The command under the proposed move below is the closest thing to a safety net. It's worth running before and after any change.

## Proposed move (not applied)

**One shared function for the display date; billing's ISO date stays separate on purpose.** Reversible (`door: two-way`).
- **What changes:** add `display_date` in a new `fixture/dates.py`. It's the current `api/serializers.py::format_date` body, unchanged. It replaces `format_date`, `date_str` and `fmt_date`.
- **Where it's called:** `api/serializers.py:6`, `jobs/export.py:6`, `web/views.py:6`. A search found no other references, aliased imports or lookups by name.
- **Steps:**
  1. Add `dates.py`.
  2. Switch the three files to use it, one commit each, running the check after each.
  3. Delete the three local helpers.
  4. Leave `billing/invoice.py` alone and add a note in `dates.py` that billing must not import it.
- **Check that behaviour holds** (run from `fixture/`; it passes today and should pass after every step):
  ```
  python -B -c "import datetime as D; from api.serializers import order_json; from jobs.export import rows; from web.views import order_page; from billing.invoice import line; o={'id':7,'placed_at':D.date(2026,3,4)}; assert order_json(o)['placed_at']=='04/03/2026'; assert rows([o])==['7,04/03/2026']; assert order_page(o)=='Order 7 placed 04/03/2026'; assert line(o)=='7|2026-03-04'; print('ok')"
  ```
  It also asserts billing's ISO output, so any change to the filing format fails it.
- **Not adding:** a date-format setting or a formatting service that billing would also go through. It would be the obvious place for someone to "unify" the two formats, which breaks the tax filing.
- **Rejected:** one date function with a format argument that billing also uses. **Cost if wrong:** one wrong argument and the authority rejects the filing. If this move itself turns out wrong, undoing it means reverting 4 small files.

**Bugs or security problems seen while reading:** none beyond the unhelpful `KeyError` in the provider registry.

Which should we look at further: the date merge, or whether to keep the provider seam at all?