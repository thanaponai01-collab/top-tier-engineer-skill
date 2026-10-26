I read all of `fixture/` (7 small Python files) and ran each formatter in a throwaway copy. Nothing in the repo was changed; the audit's checks all passed.

**Overall: messy in places.** The code is small. The one real risk is that a routine change to the date format could break the tax filing.

## What a newcomer should know before Monday

**1. Dates look like one format but are two. Don't merge them.**
- The date customers see (`dd/mm/yyyy`) is copied into three files, under three different names:
  - `api/serializers.py:1` `format_date`
  - `jobs/export.py:1` `date_str`
  - `web/views.py:1` `fmt_date`
- If you change the display format, you have to edit all three. Miss one and the API, the CSV export and the web page will show different dates.
- `billing/invoice.py:5` looks like the same helper but isn't. It must stay ISO (`yyyy-mm-dd`) because the tax authority's upload spec requires it. If it changes, the whole filing is rejected. Only a comment protects it. A search-and-replace on `strftime` would hit it too.
- I confirmed this by running all four: the three display helpers give `04/03/2026`, and billing gives `2026-03-04`.

**2. The `providers/` package isn't used by anything.**
- It has a base class, a registry and one SMTP implementation (`providers/base.py`, `registry.py`, `smtp.py`).
- Nothing outside `providers/` calls `registry.get` or `Provider`. So nothing in the repo will tell you if a change there breaks something.
- Don't build on it as if it were proven, and don't add a second provider without first finding out who calls it.

## Recommended fix (easy to undo)

**Move all display dates into one helper and leave billing alone.**
1. Add `dates.py` with `display_date(d)`, which returns `d.strftime("%d/%m/%Y")`.
2. Change the three places that use a local copy (`api/serializers.py:6`, `jobs/export.py:6`, `web/views.py:6`) to call `display_date` instead.
3. Leave `billing/invoice.py::invoice_date` as it is. Add a note in `dates.py` saying billing is a deliberate exception.

This check passes today, and should still pass after each step. Run it from `fixture/` (`-B` stops it leaving `__pycache__` files):
```
python -B -c "import datetime as D; from api.serializers import order_json; from jobs.export import rows; from web.views import order_page; from billing.invoice import line; o={'id':1,'placed_at':D.date(2026,3,4)}; assert order_json(o)['placed_at']=='04/03/2026'; assert rows([o])==['1,04/03/2026']; assert order_page(o)=='Order 1 placed 04/03/2026'; assert line(o)=='1|2026-03-04'; print('ok')"
```

**What I'm not recommending:** one shared date function for both display and billing, such as `format_date(d, kind=...)`. If that were done, a future display change could quietly change the date in the tax upload and get the filing rejected. Keeping billing separate costs one extra one-line function.

**Found in passing:** no bugs or security holes. The repo has no architecture doc or tests, so the check above is the only safety net for now.

Which do you want to explore: the display-date fix, or working out whether `providers/` should stay?