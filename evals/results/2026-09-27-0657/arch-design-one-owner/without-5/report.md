The code is small: 7 files and about 45 lines, in five areas (`api/`, `web/`, `jobs/`, `billing/`, `providers/`). Here is what a new person should know before changing anything.

## 1. Four places format dates, and one of them must never change

| File | Function | Format | Used for |
|---|---|---|---|
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` | Order page text |
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` | API JSON |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` | CSV export |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` | Tax authority filing |

- **The first three are the same function copied three times under different names.** Together they are the display date format, but nothing links them. Changing the format means editing all three, and searching for one name won't find the others. Merging them into one shared helper is a reasonable first cleanup.
- **`billing/invoice.py` is not part of that group, even though it looks like it.** The comment at `billing/invoice.py:2-4` says the tax authority's upload spec requires ISO-8601 here. If this format changes, the whole filing is rejected. Leave it out of any merge or "make dates consistent" change. It should stay its own function and keep its own format, even if the display format changes.

## 2. Some date formats are effectively public contracts
- The API (`api/serializers.py:6`) returns `placed_at` as `DD/MM/YYYY`, not ISO. That is awkward (3/4 could be read as 3 April or 4 March), but outside clients probably parse it. Changing it is a breaking API change, not a cleanup.
- The CSV export (`jobs/export.py`) probably has downstream consumers too. It also doesn't quote or escape values, so an `id` containing a comma would break the row.

## 3. The provider abstraction has only one implementation
- `providers/base.py` defines `Provider`, and its docstring says so itself: "Implemented once, by SmtpProvider." `registry.get()` defaults to `"smtp"`, and the registry holds only that entry.
- Don't treat this as a proven extension point. If you add a second provider, expect to rework the interface: `send(to, body)` returns a string, with no error handling or other options. If you're only touching SMTP, you don't need to go through the abstraction.

## 4. Practical setup notes
- **There are no tests.** Nothing will catch a date format change in any of the four places above. Adding a few tests that pin the current output, especially `invoice_date`, would help before anyone refactors.
- **Imports assume `fixture/` is the working directory.** They are written like `from providers.smtp import ...`, there are no `__init__.py` files, and there is no packaging. Run code from `fixture/` or set `PYTHONPATH`.
- **Timezones aren't handled anywhere.** `strftime` runs on whatever `placed_at` contains. Check whether those values are naive or UTC before touching date logic, especially for billing, where the date can shift near midnight.

**In short:** it's fine to merge the three display-date helpers, but keep billing separate. Treat the API and CSV formats as external contracts. Add tests before refactoring.