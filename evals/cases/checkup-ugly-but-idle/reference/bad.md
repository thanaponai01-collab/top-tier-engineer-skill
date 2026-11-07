# Structure review

The code is mostly small and readable. What to fix first:

1. legacy/tax_tables.py: sales_tax is 61 lines, complexity 25 and nests nine deep. Split it into a
   table of rates per region and category.
2. The checkout function does too much: it totals, taxes, charges and emails in one place.
3. Add type hints across the shop package.
