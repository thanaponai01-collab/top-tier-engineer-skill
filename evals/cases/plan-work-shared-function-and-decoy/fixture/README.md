# billing

A tiny invoicing library. Customers, invoices made of lines, tax by region, and a plain-text
report. Amounts are integer cents.

Everything that shows an amount asks `invoice.total()` for it; nothing else does the arithmetic.

    python -m unittest        # the suite
    python report.py          # print the sample invoices
