# Audit — fixture/

**Top move: give the customer-facing date a single owner.**

The same job is written three times under three names: `fmt_date` in
`web/views.py`, `format_date` in `api/serializers.py`, `date_str` in
`jobs/export.py`. All three return the same `%d/%m/%Y` string, nothing keeps
them in step, and a change to the display format is three separate edits today.
That is duplication of one decision, not three decisions that happen to agree.

`billing/invoice.py` must not be swept into that move. Its `invoice_date` is
ISO-8601 because the tax authority's upload format requires it, as the comment
above it records. It answers to an outside authority, so it changes for a
different reason and stays where it is; folding it in would tie a filing format
to a screen format and break the filing the first time the screen changes.

Second finding: `providers/base.py` is an interface with exactly one
implementation, `providers/smtp.py`, and one caller. Nothing in this codebase
asks for a second provider, so the seam is unpaid for — inline it until a real
second implementation turns up.

## The move, written out

- files: `web/views.py`, `api/serializers.py`, `jobs/export.py`
- owner: a new `formatting/dates.py` exporting `display_date(d)`
- callers: the three call sites in those same modules, and nothing else
- verification: run all three on one date before and after; output unchanged
- out of scope: `billing/invoice.py`, deliberately
