In `fixture/`: the dashboard is slow because `Order.total` is recomputed on every access, and the
dashboard reads it over and over. Cache it so it is computed once per order. Keep everything else
working. Don't commit.
