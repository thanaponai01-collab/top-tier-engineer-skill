"""Invoice numbers: INV-<year>-<sequence>, sequence starting at 1 each year."""


def next_invoice_number(year, last_sequence):
    return f"INV-{year}-{last_sequence + 1:04d}"
