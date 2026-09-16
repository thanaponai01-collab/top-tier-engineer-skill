# Architecture Audit — fixture/

**Messy in places.** The move that pays most: give the display date one owner.

Three modules each define the same job with a different name —
`web/views.py:1 fmt_date`, `api/serializers.py:1 format_date`,
`jobs/export.py:1 date_str` — all returning `%d/%m/%Y`. Three places to fix when
the format changes, and nothing keeps them in step today.

`billing/invoice.py:1 invoice_date` looks like a fourth copy and is not one. It
is ISO-8601 because the tax authority's upload spec fixes it, and the comment at
`billing/invoice.py:3` says so. It changes for a different reason than the
display format, so it stays separate; merging it would couple a filing format to
a customer-facing one.

`providers/base.py:1` is an abstraction with one implementation
(`providers/smtp.py`) and one caller (`providers/registry.py`). No second
provider is asked for by any requirement here, so the seam is not paid for yet.

| # | sign | where | what it costs today | move | effort |
|---|---|---|---|---|---|
| 1 | same job, three places | views.py:1, serializers.py:1, export.py:1 | a format change is three edits and can be done twice | one owner | S |
| 2 | built for "gonna need" | providers/base.py:1 | a layer that only forwards | inline until a second provider exists | S |

## Moves

Context: the display format itself is not changing; the billing format is fixed
by an external spec and is out of scope for every move below.

### 1. One owner for the display date
cost:     three copies drift; a format change is three edits
files:    web/views.py:1, api/serializers.py:1, jobs/export.py:1
owner:    a new `formatting/dates.py` with `display_date(d)`
callers:  web/views.py:5, api/serializers.py:5, jobs/export.py:5
proof:    run the three modules on one order; same output as before the move
effort:   S
after:    nothing
