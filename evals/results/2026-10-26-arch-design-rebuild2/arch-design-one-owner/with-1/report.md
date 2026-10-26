I ran the audit over `fixture/` and it's finished. The skill's checks all pass, and nothing in `fixture/` was changed: I ran my checks in a throwaway copy, with no `__pycache__` left behind.

**Overall:** messy in places. The code is small and readable (7 files, 45 lines), but it has one trap that a sensible-looking cleanup would set off. There's no architecture doc in the repo to check against.

## What a new person should know before Monday

**1. There are four date formatters, and the obvious cleanup breaks things.**
- `web/views.py:1`, `api/serializers.py:1` and `jobs/export.py:1` each have their own copy of the same day/month/year format (`"%d/%m/%Y"`). Changing the date format customers see means editing all 3 files.
- `billing/invoice.py:1` looks like a fourth copy, but it isn't. It uses the year-month-day format (ISO-8601) because the tax authority's upload spec requires it. The comment at `billing/invoice.py:2-4` says changing it rejects the whole filing. **Never fold it into a shared helper.**
- Two of the three matching copies are probably promises to outside users, not just how dates look on screen: the API's `placed_at` field in JSON, and the CSV export. If you merge all three, changing the web page's date format would also change what API clients and export consumers read.
- No tests check any of the four outputs, so either mistake would ship with nothing failing.

**2. The message-sending code is built for many providers but has one.** `providers/base.py`, `registry.py` and `smtp.py` add up to three files for one SMTP sender, and nothing in the repo calls `registry.get`. Don't add more structure around it until a second provider actually exists.

**3. Imports only work from inside `fixture/`.** Imports are written like `from providers.smtp import ...`, so code has to run with `fixture/` as the working directory or on the Python path.

## Recommended move: pin every date output before anyone removes the duplicates
- **What it changes:** a new test file, `tests/test_date_contracts.py`. No production code changes.
- **Steps:**
  1. Add tests that run each formatter on 2 Jan 2026 and check the result:
     - `order_page` gives `02/01/2026`
     - `order_json`'s `placed_at` gives `02/01/2026`
     - `rows` gives `1,02/01/2026`
     - `line` gives `1|2026-01-02`
  2. Ask the owner whether the API and export formats are meant to follow the web page. Only merge the copies that are.
- **Callers:** each formatter is used only in its own file (`web/views.py:6`, `api/serializers.py:6`, `jobs/export.py:6`, `billing/invoice.py:9`). Nothing else in the repo calls `order_page`, `order_json`, `rows` or `line`.
- **Check that behaviour holds:** this command passes today and should pass after each step. Run it from inside `fixture/`:
  ```
  python -B -c "import datetime as t; from web.views import order_page; from jobs.export import rows; from api.serializers import order_json; from billing.invoice import line; o={'id':1,'placed_at':t.date(2026,1,2)}; assert order_page(o)=='Order 1 placed 02/01/2026'; assert rows([o])==['1,02/01/2026']; assert order_json(o)['placed_at']=='02/01/2026'; assert line(o)=='1|2026-01-02'; print('ok')"
  ```
- **Easy to undo:** yes, it only adds a test.
- **What it reuses:** nothing. There are no tests and no shared formats module yet.
- **What it avoids adding:** a shared date helper. That helper would quietly control the API and CSV formats too, and invite folding billing in.
- **Not doing:** merging the three matching copies now. If that call is wrong, one change to the web date format becomes an unflagged breaking change to API clients and the CSV export. If billing gets swept in, the tax filing is rejected.

**Seen in passing:** no bugs or security holes. One caution: nothing in the repo calls any of these functions, so everything above was read from the code or run directly, not watched through a real request.

Which should we explore: the pinning tests (and the format question for the owner), or trimming the provider code down?