I read all 7 files in `fixture/` (45 lines total). It's small, but there are three things a newcomer could easily get wrong.

## Layout

| Area | File | What it does |
|---|---|---|
| `api/` | `serializers.py` | Builds order JSON. The date is `%d/%m/%Y`. |
| `web/` | `views.py` | Renders the order page text. The date is `%d/%m/%Y`. |
| `jobs/` | `export.py` | Writes order CSV rows. The date is `%d/%m/%Y`. |
| `billing/` | `invoice.py` | Writes pipe-delimited tax filing lines. The date is `%Y-%m-%d`. |
| `providers/` | `base.py`, `smtp.py`, `registry.py` | Message-sending setup: a base class, one SMTP implementation and a lookup by name. |

There's no shared or utility module, no tests, and no `__init__.py` files.

## What they should know before changing things

**1. The display date format is copied into three places.**
`api/serializers.py:1`, `web/views.py:1` and `jobs/export.py:1` each have their own helper (`format_date`, `fmt_date`, `date_str`), and all three return `%d/%m/%Y`. Nothing ties them together. If someone changes the format in one file, the others stay as they were, and the API, the web page and the CSV export end up showing different dates.

**2. The billing date looks like a fourth copy, but it must stay separate.**
`billing/invoice.py:1-5` looks like the same helper with a different format. The comment there explains why it isn't: the tax authority's upload spec requires ISO-8601, and changing this field gets the whole filing rejected. This is the biggest trap in the codebase. The obvious cleanup for point 1 is to merge all the date helpers into one, and doing that carelessly would tie tax filings to the customer-facing format. If someone does merge them, it should cover only the three display helpers. `invoice_date` should stay apart, and ideally get a test that pins the format to `YYYY-MM-DD`.

One open question to ask whoever owns `jobs/export.py`: who reads that CSV? If it's a person, the date belongs with the display format. If it's another system, it's a machine contract like billing's and shouldn't follow display changes either. Nothing in the code says which.

**3. `providers/` is set up for more providers than it has.**
`Provider` has exactly one subclass, and its own docstring says so ("Implemented once, by SmtpProvider"). `registry.get()` defaults to `"smtp"`. Adding a provider means subclassing `Provider` and adding it to `PROVIDERS`. Until a second provider exists, the base class and registry don't do much, so they don't need extra work. Nothing in `fixture/` actually calls the registry yet.

## Practical notes

- **Imports:** they're absolute (`from providers.smtp import ...`), so code has to run with `fixture/` as the working directory or on `PYTHONPATH`. There are no `__init__.py` files, so these load as Python 3 namespace packages.
- **Data shape:** orders are plain dicts with `id` and `placed_at` keys, where `placed_at` is a `datetime`/`date`. There's no model or schema, so renaming a key means updating all four modules by hand.
- **No tests:** I didn't run anything because there's nothing to run. A cheap first step would be one test per output (API, web, CSV, invoice) that pins its date format, so changes like those in points 1 and 2 fail loudly.