`fixture/` is small: 7 Python files, 45 lines in total, in five areas. Before a new person changes anything, they should know these things.

## 1. The date formatting looks duplicated, and only some of it is

Four functions turn a date into a string:

| File | Function | Format | Used for |
|---|---|---|---|
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` | API JSON |
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` | Customer-facing page |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` | CSV export |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` | Tax filing |

Merging these into one shared `format_date` looks like an easy cleanup. Here is what's actually safe:

- **The three `%d/%m/%Y` copies really are duplicates.** Putting them in one shared helper is reasonable, and it means a future change to the display format happens in one place instead of three.
- **`billing/invoice.py` must stay separate.** Its comment (`invoice.py:2-4`) explains why: the tax authority's upload spec requires ISO-8601. It is not a display format, and if it changes the whole filing gets rejected. If someone builds a shared date helper, billing should not use it, even with a "format" parameter. Otherwise a later change to the display default could reach it.
- **Each of the other three needs its own decision.** Should the API and the CSV export follow the website's format, or are they contracts with other systems? Nothing in the code says. If an outside consumer parses the API's `placed_at` or the export file, changing their format is a breaking change. Find out who reads them before you treat them as display formats.

## 2. `providers/` is built for many providers but has only one

- `base.py` defines an abstract `Provider`, `registry.py` maps names to classes, and `smtp.py` is the only implementation. The base class docstring says so: "Implemented once, by SmtpProvider."
- Don't add features to this layer, and don't build more abstraction on it, unless a second provider is actually coming. To add one, subclass `Provider`, implement `send(to, body)` and add it to `PROVIDERS`.
- `get()` defaults to `"smtp"` and raises a bare `KeyError` if the name is unknown.

## 3. Practical setup points

- **There are no tests.** Nothing checks the billing format, so the comment in `invoice.py` is the only protection. A good first contribution would be a test that fixes `invoice_date` to `YYYY-MM-DD`, written before anyone refactors the date code.
- **There are no `__init__.py` files** and no packaging. Imports like `from providers.smtp import ...` only work when you run from inside `fixture/` (Python 3 treats these folders as namespace packages).
- **Orders are plain dicts** with `id` and `placed_at` (a `date`/`datetime`). There's no model class or validation, so a missing key fails with a `KeyError` wherever it's first used.
- **The output formats are built by hand.** The CSV in `jobs/export.py` and the pipe-separated invoice line in `billing/invoice.py` do no escaping or quoting. That's fine while `id` is a simple value, but it will produce broken output if an id ever contains `,` or `|`.

**In short:** the date code isn't four copies of one thing. Three of the functions might share code, and billing must keep its own format, so merge carefully. Everything else is small and simple, but there are no tests, so add them before refactoring.