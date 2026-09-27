The codebase is small: 7 files and 45 lines of Python, in five top-level packages that don't import each other. There are no tests, no `__init__.py` files, no dependency manifest, no README and no git history. That means the code is the only documentation, and nothing will catch a mistake. Here's what I'd tell someone starting Monday.

## 1. The date-formatting duplication is a trap

Four places turn an order's `placed_at` into a string:

| File | Function | Format | Who reads it |
|---|---|---|---|
| `web/views.py:2` | `fmt_date` | `%d/%m/%Y` | People, on the order page |
| `api/serializers.py:2` | `format_date` | `%d/%m/%Y` | API clients (JSON) |
| `jobs/export.py:2` | `date_str` | `%d/%m/%Y` | Whoever consumes the CSV export |
| `billing/invoice.py:5` | `invoice_date` | `%Y-%m-%d` | The tax authority's upload system |

The obvious cleanup is to merge these into one `format_date` helper. **Don't.**

- **Billing must stay separate.** The comment at `billing/invoice.py:2-4` says this field is fixed as ISO-8601 by the tax authority's upload spec, and changing it rejects the whole filing. It's the only place in the codebase that explains why it looks the way it does. Treat it as a hard constraint, not as inconsistency to tidy up.
- **The other three only match by coincidence, as far as the code shows.** One is a page people read, one is a public API contract, and one is a file format some downstream system parses. If they share a helper, a harmless display change (say, "27 Sep 2026" on the web page) would silently change the API response and the CSV export. That breaks clients nobody in this repo can see.
- **Before changing any of the three, find out who consumes it.** In particular, `dd/mm/yyyy` in a JSON API is unusual and ambiguous (is 03/04 March or April?). It looks like it was copied from the web view rather than chosen. It might be worth fixing, but it's a breaking API change and needs versioning or coordination, not a quick refactor.

If you do add a shared helper, give it a specific name (e.g. `display_date`) and have only the web view use it.

## 2. `providers/` is an abstraction with one implementation

- `Provider` (`providers/base.py`) is an abstract base class whose docstring says it's "Implemented once, by SmtpProvider".
- `registry.py` maps a single key, `"smtp"`, and defaults to it.
- Nothing in `fixture/` imports `providers` at all. It's either used from outside this directory or it's dead code. Check before you change or delete it.

Don't read the registry as a sign that several providers exist or are planned. Also, `registry.get()` creates a new `SmtpProvider` on every call, which matters if SMTP ever gains connection state.

## 3. Implicit conventions

- **Orders are plain dicts** with `"id"` and `"placed_at"` (a `datetime`) keys, and every module indexes them directly. There's no model class or schema, so renaming a key means grepping all four modules by hand.
- **Imports are absolute from the `fixture/` root** (`from providers.smtp import ...`). Code only runs with `fixture/` on `PYTHONPATH`, and it relies on implicit namespace packages because there are no `__init__.py` files.
- **Output formats are built by hand.** The CSV uses f-strings joined with `,` (`jobs/export.py:6`) and the invoice uses `|` (`billing/invoice.py:9`), with no escaping. It works while the fields are an id and a date. Any free-text field (a customer name with a comma, say) will corrupt the file, so switch to `csv` or proper encoding before adding one.

## 4. Before making changes

1. **Add tests that pin the output of each format**: the web string, the API JSON, the CSV rows and the invoice line. In a codebase this small they take minutes to write, and they're the only thing that would catch someone "fixing" the duplication in section 1.
2. **Initialise git** (there's no repo yet) so changes can be reviewed and reverted.
3. **Write down who consumes each output** (web, API, CSV export, invoice). The billing comment is the model to follow: say who reads it and what breaks if it changes.