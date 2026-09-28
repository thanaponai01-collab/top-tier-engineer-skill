There are seven small Python files, about 45 lines in total. It's small enough to read in ten minutes, and they should read all of it. Here is what I'd tell them before they change anything.

## 1. There are four date formatters, and one of them must not change

| File | Function | Format |
|---|---|---|
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` |
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` |

- **`billing/invoice.py` is load-bearing.** The comment says the tax authority's upload spec requires ISO-8601, and any other format rejects the whole filing. It looks just like the other three, so someone tidying up could easily fold it into a shared helper. Don't.
- **The other three are copies of the same code under three names.** Nothing links them. If someone changes "the date format" and edits only one, the outputs will drift apart without anything failing.
- **Being textually identical doesn't mean they should change together.** Each has different consumers:
  - `web` is what users see on the page.
  - `api` is a JSON contract, so changing it is a breaking change for API clients. (Also, `dd/mm/yyyy` in JSON is unusual and ambiguous. Treat it as existing behaviour that clients may depend on, not something to quietly "fix".)
  - `jobs/export` produces CSV rows that some downstream system probably parses. Nothing in the repo says what that system is.

  Merging them into one helper is reasonable only once someone confirms they really should always stay in sync. Until then, a change to any one of them should be a deliberate decision about that one output.

## 2. `providers/` is abstraction with only one user
- `Provider` (`providers/base.py`) is a base class, and its own docstring says it is "Implemented once, by SmtpProvider."
- `registry.PROVIDERS` has a single entry, and `get()` defaults to `"smtp"`.
- It's harmless, but it's structure for providers that don't exist yet. To add a provider: subclass `Provider`, implement `send(to, body)`, and register it in `PROVIDERS`. Otherwise, don't feel you need to route new code through it or add more layers on top.
- `SmtpProvider.send` just returns a string (`"smtp:{to}:{body}"`) and doesn't send anything. It's either a stub or a test double. Check which before relying on it.

## 3. Missing safety nets
- **No tests.** Nothing will catch a format regression, including the billing one. If they change anything date-related, a first useful contribution would be a test that pins `invoice_date` to `YYYY-MM-DD`.
- **No `__init__.py` or packaging.** The imports look like `from providers.smtp import ...`, so the code only works when run with `fixture/` as the working directory or on `PYTHONPATH`.
- **No git history** in this directory, so there's no blame or commit log to explain past decisions. The billing comment is the only written record of why anything is the way it is.
- **Order data is a plain dict** (`order["id"]`, `order["placed_at"]`) with no schema. Every module assumes `placed_at` is a `datetime`/`date`, and nothing checks it.

## Short version for Monday
1. Never change `billing/invoice.py`'s date format.
2. The three `%d/%m/%Y` copies aren't linked. Decide deliberately which ones a change should affect, and remember that `api` and `export` have outside consumers.
3. `providers/` has only one implementation, so don't over-invest in it.
4. There are no tests, so add them before you refactor.