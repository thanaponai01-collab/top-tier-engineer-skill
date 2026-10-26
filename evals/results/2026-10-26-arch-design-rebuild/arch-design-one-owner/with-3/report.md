## What a new person should know before changing `fixture/`

**Overall: messy in a few places, but small.** The codebase is 7 files and 45 lines. The real danger isn't size. It's one function that looks like a duplicate and must not be treated as one. The audit gate passed, and nothing in the repo was changed.

### 1. Do not merge the invoice date with the other date functions
`billing/invoice.py:1` formats dates as `%Y-%m-%d`. The tax authority's upload spec fixes that format. The other three date functions (below) all use `%d/%m/%Y` and are true copies of each other. When a newcomer sees four date formatters, the obvious cleanup is to make them one function. If `invoice_date` gets folded in, the next change to the display format also changes the tax field, and the whole filing gets rejected. The comment in the file says this, but it's easy to miss when deduplicating.

### 2. The date format customers see is copy-pasted in three places
- `api/serializers.py:1` `format_date`
- `web/views.py:1` `fmt_date`
- `jobs/export.py:1` `date_str`

All three are the same `strftime("%d/%m/%Y")` under different names. Changing the display format means editing 3 files. Miss one and the API, the web page and the CSV export show different dates. Also, the CSV export may feed someone else's import. Check who reads it before changing its format.

### 3. The provider layer has exactly one implementation
`providers/base.py`, `registry.py` and `smtp.py` use three files for a single SMTP send. Adding a new channel means one class plus one entry in the registry, so the extra layer is cheap. Leave it alone; it's not worth removing.

### Proposed move: one shared display-date formatter, with billing excluded
- **Changes:** add a new `display_date` in `dates.py`. Then point `format_date`, `fmt_date` and `date_str` at it one file at a time. Their callers are `api/serializers.py:6`, `web/views.py:6` and `jobs/export.py:6`.
- **Reuses:** the body of `api/serializers.py:1`, which already does this job.
- **Never touch:** `billing/invoice.py::invoice_date`, or its comment.
- **Risk:** low and easy to undo. No stored data and no public API change.
- **Not doing:** one date helper for every format, billing included. If that were done, a display change would break the tax filing.
- **Proof:** I ran this in a throwaway copy and it passes today. Run it from `fixture/` after each step:
  ```
  python -B -c "import sys; sys.path.insert(0,'.'); from datetime import date; from api.serializers import order_json; from web.views import order_page; from jobs.export import rows; from billing.invoice import line; o={'id':7,'placed_at':date(2026,3,4)}; assert order_json(o)['placed_at']=='04/03/2026'; assert order_page(o)=='Order 7 placed 04/03/2026'; assert rows([o])==['7,04/03/2026']; assert line(o)=='7|2026-03-04'; print('ok')"
  ```
  The billing assert is the important one: it fails if the invoice date ever starts following the display format.

### Other things worth knowing
- **There are no tests.** The command above is the only safety net.
- **Imports assume `fixture/` is the import root**, e.g. `from providers.smtp import ...`. Run code from inside `fixture/`, or code that uses the providers won't import.
- **There's no architecture doc or ADR** in the repo. Once a move lands, it's worth writing a short ADR on why the invoice date stays separate, since that reason won't go away.
- **Small bug seen in passing:** `providers/registry.py:7` throws a bare `KeyError` for an unknown provider name instead of a clear error.

Do you want me to go ahead with the shared date formatter, or look into something else first?