`fixture/` is small: 7 Python files and about 45 lines in total. There are no tests, no README and no packaging. There are two things worth knowing before changing anything: how dates are formatted, and the provider layer.

## 1. Dates: three copies of one format, plus one that must stay different

| File | Function | Format | Purpose |
|---|---|---|---|
| `api/serializers.py:1` | `format_date` | `%d/%m/%Y` | JSON returned by the API |
| `web/views.py:1` | `fmt_date` | `%d/%m/%Y` | Customer-facing order page |
| `jobs/export.py:1` | `date_str` | `%d/%m/%Y` | CSV export rows |
| `billing/invoice.py:1` | `invoice_date` | `%Y-%m-%d` | Tax-authority filing |

**What to know:**

- **The display format is copied in three places under three different names.** Changing it means finding and updating all three, and searching for one name won't turn up the others. Merging them into one shared helper is a sensible first cleanup.
- **`billing/invoice.py` must never join that helper.** It looks like the same kind of function, but the comment at `billing/invoice.py:2-4` explains that the tax authority's upload spec requires ISO-8601. If it changes, the whole filing is rejected. If you merge the date helpers, leave billing out on purpose and keep that comment. Anything that touches billing should be checked against the filing spec, not against the display format.
- **Check who reads the export before tying it to the display format.** `jobs/export.py` uses the display format today, but it writes CSV, which another system may be parsing. If you point it at a shared display helper, any later change to the display format will also change the export's output. Find out who consumes the CSV first. It may need its own fixed format, like billing has.
- **These are UK/European-style dates.** `%d/%m/%Y` is day/month/year, so `03/04/2026` is 3 April. Anyone used to US dates should keep that in mind when reading output or writing fixtures.

## 2. The provider layer has exactly one provider

`providers/base.py` defines an abstract `Provider`. `SmtpProvider` is its only implementation, and `providers/registry.py` maps the name `"smtp"` to it, with `get()` defaulting to `"smtp"`.

- The base class docstring says so directly: "Implemented once, by SmtpProvider." This is a single SMTP sender behind a plugin layer, not a real plugin system. Don't build more on top of it unless a second provider is actually coming.
- **Adding a provider means:** subclass `Provider`, implement `send(to, body)`, and register it in `PROVIDERS`.
- **Unknown names aren't handled.** `get("foo")` raises a plain `KeyError`.
- **`send` doesn't actually send anything.** It returns a string (`"smtp:{to}:{body}"`). Treat it as a stub, not real email delivery.

## 3. General conventions and gaps

- **Orders are plain dicts** with `"id"` and `"placed_at"` keys, where `placed_at` is a `datetime`/`date`. There is no model class or validation, so a missing key raises `KeyError` and a string date fails at `.strftime`.
- **Imports assume the `fixture/` folder is on the Python path** (e.g. `from providers.smtp import ...`). There are no `__init__.py` files, so this relies on namespace packages. Run code from `fixture/`, or it won't import.
- **There are no tests.** Before cleaning up the date helpers, it's worth adding a small test that pins each output format, and above all one that keeps billing's ISO format fixed. That's the change most likely to break something unnoticed.

**Short version:** the three display-date helpers are duplicates and safe to merge; billing's date must stay separate; check who reads the CSV export before changing its format; and the provider layer is a stub with one implementation, so keep it simple.