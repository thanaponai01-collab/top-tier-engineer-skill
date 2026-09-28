The code is small: 7 files and 45 lines of code in total. The main thing a new person needs to know is how dates are formatted, because the same format string appears in several places and one lookalike copy must not be touched.

## 1. Dates: three copies of one format, plus one that only looks like a copy

| File | Function | Format | Output goes to |
|---|---|---|---|
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` | JSON API responses |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` | CSV export rows |
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` | HTML order page |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` | tax authority filing |

- **The customer-facing format is copied, not shared.** Three files each define it under a different name. If someone asks you to change how dates look, you need to change all three. Searching for one function name won't find the other two, so search for `strftime` instead.
- **Leave `billing/invoice.py` out of any cleanup.** It looks like a fourth copy, but the comment at `billing/invoice.py:2-4` says the tax authority's upload spec requires ISO-8601. Changing it gets the whole filing rejected. If you create a shared `display_date()` helper (a reasonable idea), billing must not use it.
- **The three copies probably shouldn't all be treated as display formatting.** The API response and the CSV export are likely read by other programs, such as API clients and whatever imports the CSV. Changing their format could break those consumers, even though changing the web page is harmless. Check with whoever owns those consumers first. It's also worth knowing that `dd/mm/yyyy` is ambiguous (US readers see it as mm/dd), which matters for an API.

## 2. `providers/` has a plug-in structure with only one plug-in

- `Provider` in `base.py` is a base class, `registry.py` maps names to providers, and `SmtpProvider` in `smtp.py` is the only implementation. The docstring says so directly: "Implemented once, by SmtpProvider."
- `registry.get()` defaults to `"smtp"`, and an unknown name raises a bare `KeyError`.
- So there is no hidden second provider to worry about. To add one, subclass `Provider`, implement `send`, and add it to `PROVIDERS`.

## 3. No tests or project setup to lean on

- There are no tests, no README, no dependency file, and no `__init__.py` files. The folders only import as packages because Python 3 allows packages without `__init__.py` ("namespace packages").
- Imports are absolute (`from providers.base import …`), so code has to be run with `fixture/` as the working directory or on `PYTHONPATH`.
- It's not under version control, so there's no history to explain past decisions.
- Before changing any date code, a good first step is to add small tests that fix the current output of each formatter, especially `invoice_date`. That way a well-meant cleanup can't quietly change the billing format.

## Short version for Monday

1. The customer date format is copied into 3 files. Search for `strftime`, not a function name.
2. The billing date format is fixed by an outside regulator. Never merge it into a shared helper or change it.
3. The API and CSV formats may be contracts with other systems. Check who reads them before changing them.
4. There are no tests, so add them before refactoring.