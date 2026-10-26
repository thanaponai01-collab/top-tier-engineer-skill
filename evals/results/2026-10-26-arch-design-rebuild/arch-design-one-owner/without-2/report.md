`fixture/` is small: 7 Python files, about 45 lines in all. It covers two things, date formatting for orders and a message-sending provider layer. Neither has tests, `__init__.py` files, a README or config. Here is what a new person should know before changing anything.

## 1. Never merge `billing/invoice.py`'s date format with the others

This is the most important point. Four functions format `order["placed_at"]`, and they look like copies of each other:

| File | Function | Format |
|---|---|---|
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` |
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` |

The obvious cleanup is to replace them with one shared `format_date` helper. For the first three, that's fine and worthwhile. They are the customer-facing display format, and right now changing it means editing three places and hoping none are missed.

**`invoice_date` must stay separate.** Its comment (`billing/invoice.py:2-4`) says the tax authority's upload spec requires ISO-8601. If it changes, the entire filing is rejected. Folding it into a shared helper, or "fixing" it to match the display format, would quietly break tax filings. Nothing else in the code protects it: there is no test and no type, only that comment.

**Suggestion:** if you consolidate, give the result an explicit name like `display_date`. Keep `invoice_date` where it is, ideally with a test that pins it to `YYYY-MM-DD`.

**Open question for the team:** `jobs/export.py` uses the display format. Is that export read by people, or by another system? If a machine parses it, it may have its own format requirement that just happens to match the display format today. Find out before you tie it to the display helper.

## 2. The provider layer is an abstraction with only one implementation

- `providers/base.py` defines `Provider.send`, and its docstring says outright that only `SmtpProvider` implements it.
- `providers/registry.py` maps `"smtp"` to `SmtpProvider`. `get()` defaults to `"smtp"`, and an unknown name raises a bare `KeyError`.
- `SmtpProvider.send` (`providers/smtp.py:5`) doesn't actually send anything. It returns the string `"smtp:{to}:{body}"`, so it's a stub or placeholder.

What this means for you:
- Adding a new provider is cheap: subclass `Provider` and add it to `PROVIDERS`.
- Don't build more machinery on top (plugin discovery, config-driven selection and so on) until there's a second provider that needs it.
- Don't assume mail goes out anywhere real.

## 3. Practical points

- **Imports:** they're absolute (`from providers.smtp import ...`) and there are no `__init__.py` files. The code only works if you run it with `fixture/` as the working directory or on `PYTHONPATH`.
- **Order data:** orders are plain dicts with an `id` key and a `datetime` in `placed_at`. There's no model class or validation, so a missing key fails with a `KeyError` wherever it's first accessed.
- **No tests:** any refactor, including the date consolidation above, should start by adding tests. The invoice format test matters most.

## Short version

- The three display-date helpers are real duplication and safe to merge.
- The billing date only looks like duplication. It's set by a legal requirement and must not change.
- The provider registry is mostly scaffolding around a stub.