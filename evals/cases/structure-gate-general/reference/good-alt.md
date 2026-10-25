Short answer: mostly fine, with one real knot.

The knot is `compute_price` in `pricing.py`: a 64-line function with about thirty if/elif
branches nested six levels deep. Line pricing, coupons, shipping and tax all live in it, and the
only test exercises one path. Adding a discount type means threading another condition through it,
and you won't know what you broke.

Two smaller things:
- `models.py` and `store.py` import each other — a circular import. Today it loads, but neither
  module can be used or tested on its own.
- `export_csv.py` and `export_json.py` repeat the same invoice-normalising block. Fix a rounding
  rule in one and the other keeps the old behaviour.

The rest of the code (the CLI, the page script, the write functions) is small and clear.
