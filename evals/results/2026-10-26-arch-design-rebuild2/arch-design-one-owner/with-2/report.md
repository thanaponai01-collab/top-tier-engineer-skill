The codebase is small (7 files, 45 lines) and mostly fine. The main thing a new person needs to know is that the date helpers look like duplicates, but they aren't all interchangeable, and merging them would break things outside the code.

## What to know before Monday

**1. Of the four date formatters, one must never change, and it sits right next to the other three.**
- Three files print dates as `31/01/2026`, each in its own function with its own name:
  - `api/serializers.py:1` `format_date`
  - `jobs/export.py:1` `date_str`
  - `web/views.py:1` `fmt_date`
- `billing/invoice.py:1` `invoice_date` prints `2026-01-31`. The comment at `billing/invoice.py:2-4` says the tax authority requires this format, and that changing it gets the whole filing rejected.
- Changing the date format customers see means editing 3 files today. The obvious cleanup is one shared helper, which is exactly how the billing format would get changed by accident.
- Two of those three "display" copies are also read by other systems: the API JSON and the export rows. So they may be contracts too, not just what appears on screen.
- Nothing enforces any of this. There are no tests in the repo; the only guard is that comment.
- I ran all four formatters in a temporary copy to confirm the outputs.

**2. `providers/` is a plugin setup with only one plugin.**
- `base.py`, `registry.py` and `smtp.py` exist so the code can look up `SmtpProvider` by the string `"smtp"`.
- Nothing in this repo calls `providers.registry.get`. Whoever uses it lives outside the repo, so treat its signature as something other code depends on.
- Don't add a second provider type, or remove this setup, without finding those callers first.

## Recommended first change
**Add tests that lock in each date format before anyone merges the date helpers.** This change can be undone freely.

1. **Add the tests.** Create `tests/test_date_formats.py` with four checks:
   - billing produces `id|YYYY-MM-DD`, labelled with the tax-authority reason;
   - the API, the export and the web page each produce `DD/MM/YYYY`.

   No source code changes.
2. **Ask before merging.** Ask the product owner whether the API and the export are allowed to change whenever the on-screen format does. Only if the answer is yes, make `jobs/export.py` and `web/views.py` use `api/serializers.py::format_date`. That's a 2-file edit the tests will check.

- **Proof:** run this from the `fixture/` folder. It passes on today's code; run it again after each step:
  ```
  python -B -c "import datetime as D; from api.serializers import order_json; from web.views import order_page; from jobs.export import rows; from billing.invoice import line; o={'id':7,'placed_at':D.date(2026,1,31)}; assert order_json(o)['placed_at']=='31/01/2026'; assert order_page(o)=='Order 7 placed 31/01/2026'; assert rows([o])==['7,31/01/2026']; assert line(o)=='7|2026-01-31'; print('ok')"
  ```
- **What I'm not recommending:** a shared `dates/formats.py` helper used by all four today. If it guessed wrong, one edit would quietly change the public API and the export file, and if billing were included, it would get every tax filing rejected.

**Found in passing:** no bugs or security holes. One small thing: `providers.registry.get("unknown")` crashes with a bare `KeyError` instead of a clear error message.

Nothing in the repo was changed; my checks ran in a temporary copy. The repo has no `docs/architecture.md`, so there was no existing architecture doc to check.

**Which should we look at next: the date-format tests, or tracking down who calls `providers` from outside the repo?**