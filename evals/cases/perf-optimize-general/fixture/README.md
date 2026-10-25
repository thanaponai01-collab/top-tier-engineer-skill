# Nightly sales report

`python report.py data/orders.csv` prints the order count, revenue by region with tax, and the
top five customers by spend. Finance pastes the output into the month-end pack.

- `data/orders.csv` is last night's export from the shop. The export retries, so the same
  `order_id` can appear more than once; count each order once, and the first row is the real one.
- `data/regions.csv` holds each region's name and tax rate.

Tests: `python -m unittest discover tests`
