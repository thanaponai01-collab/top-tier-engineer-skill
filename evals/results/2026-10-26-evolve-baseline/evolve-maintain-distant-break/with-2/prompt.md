Use `evolve-maintain` in `fixture/`: the dashboard is slow because `Order.total` is recomputed on
every access, and the dashboard reads it over and over. Cache it so it is computed once per order.
Keep everything else working. Don't commit.

The explicitly requested evolve-maintain skill is at <tmp>\tte-plugin-4qpmch93\verify-loop\skills\evolve-maintain\SKILL.md. Read and follow that SKILL.md before starting.
