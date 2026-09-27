I read all 7 files in `fixture/` (45 lines of Python). There are two things a newcomer needs to understand before changing anything, and one of them can break the tax filing if they get it wrong.

## 1. Date formatting: four copies, and one must stay different

Four functions turn a date into a string:

| File | Function | Format |
|---|---|---|
| `fixture/api/serializers.py:1` | `format_date` | `%d/%m/%Y` |
| `fixture/web/views.py:1` | `fmt_date` | `%d/%m/%Y` |
| `fixture/jobs/export.py:1` | `date_str` | `%d/%m/%Y` |
| `fixture/billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` |

The API, web and export copies are identical and share nothing. Changing the display date format means editing all three, and it's easy to miss one. Merging them into one helper is a fair cleanup.

**The billing function must stay out of any merge.** Its comment (`fixture/billing/invoice.py:2-4`) says the ISO-8601 format is fixed by the tax authority's upload spec. It must not follow the customer-facing format, and changing it rejects the whole filing. The two formats only differ by chance today. Someone who sees four date helpers and makes them all call one function will break tax filings.

Before merging the other three, check who reads the export in `jobs/export.py`. A CSV export often goes to another system that parses the date, so it may need to stay fixed even if the web or API format changes.

## 2. The providers package is set up for more than it has

- `Provider` in `providers/base.py` is a base class with a single subclass, `SmtpProvider`. Its own docstring says so.
- `registry.get()` defaults to `"smtp"`. An unknown name raises a plain `KeyError`, not a clear error message.
- You don't need to add more layers when you touch this code. If you add a second provider, register it in `PROVIDERS` in `registry.py`.
- Imports are absolute (`from providers.smtp import ...`) and there are no `__init__.py` files. The code only works when `fixture/` itself is on the import path, so running from the repo root or importing it as `fixture.providers` will fail.

## Other things to know

- **There are no tests, README or config files.** Nothing will catch a changed date format or a broken import, so check behaviour by hand or add tests before refactoring.
- **Orders are plain dicts** with keys `id` and `placed_at` (a date or datetime), used the same way in all four modules. A missing key fails with a `KeyError` wherever it's first read.
- **Each top-level folder** (`api`, `web`, `jobs`, `billing`, `providers`) is separate and none imports another. Only `providers` is linked internally.

**In short:** the dates in API, web and export can change together, but the billing date should never change. The rest is small and easy to follow.