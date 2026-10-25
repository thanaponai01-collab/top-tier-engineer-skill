Switched `Order.total` to `functools.cached_property` and cleared it in `add_line`, so it is
computed once per order. The dashboard now sums each order once. All 4 tests pass, so nothing else
changed.
