`fixture/` is small: 7 Python files, 45 lines, in five packages. There are no tests, no `__init__.py` files and no README. Most of what a new person needs to know is about one thing: date formatting.

## 1. Four date helpers look like duplicates, but only three of them are

| File | Function | Format | Output goes to |
|---|---|---|---|
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` | Customer-facing order page |
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` | API JSON (`placed_at`) |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` | CSV export rows |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` | Tax authority filing |

Most people's first instinct will be to merge these into one shared `format_date`. Before doing that, they should know:

- **Leave `billing/invoice.py` out of any merge.** Its comment (`billing/invoice.py:2-4`) says the ISO-8601 format is fixed by the tax authority's upload spec. It must not change when the display format changes, and changing it "rejects the whole filing." It's the only helper with a different format, and that difference is deliberate. If anyone merges it into a shared helper, or later changes the shared format, tax filings will fail.
- **Merging the other three is reasonable, but check the consumers first.** The web view is plainly display text. The API response and the CSV export, though, are probably read by other programs: API clients, and whoever imports the export. They use `dd/mm/yyyy` today, most likely because the code was copy-pasted, not because anyone specified it. If you tie them to a shared "display format," a future change to how dates look on screen would quietly break those programs' contracts. Find out who reads each output before deciding which helpers should share a format.
- A useful rule of thumb: **group helpers by who reads the output, not by whether the code looks the same.**

## 2. The provider abstraction has only one implementation
- `providers/base.py` defines an abstract `Provider`. Its docstring says it is "Implemented once, by SmtpProvider."
- `providers/registry.py` maps `"smtp"` to `SmtpProvider`, and `get()` defaults to `"smtp"`. An unknown name raises a plain `KeyError`.
- To add a provider, subclass `Provider`, implement `send(to, body)`, and register it in `PROVIDERS`. The layer is a bit speculative for a single backend, but it costs almost nothing. It isn't worth removing, and it isn't worth expanding until a second provider actually exists.

## 3. Practical setup notes
- **Import paths:** the code uses `from providers.smtp import ...`. That means it expects `fixture/` itself to be on `sys.path`, not the repo root, and it has no `__init__.py` files (it relies on namespace packages). Run code from inside `fixture/` or set `PYTHONPATH=fixture`.
- **Data shape:** every module passes orders around as plain dicts with `id` and `placed_at`, where `placed_at` is a `date` or `datetime`. There's no model class, so a field rename has to be made in all four modules by hand.
- **No tests.** Before refactoring the date helpers, add a small test that pins each module's exact output, especially the billing line (`"<id>|YYYY-MM-DD"`). That way an accidental format change fails loudly instead of showing up as a rejected filing.

**In short:** the obvious cleanup (one date helper) is only safe for part of the code. Keep billing's format separate, and check who consumes the API and CSV outputs before you merge anything.