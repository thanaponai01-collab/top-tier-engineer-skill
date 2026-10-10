# Run report

Goal matched to the playbook for a defect whose cause is unknown, so diagnosis comes before any
fix. I wrote down what done means first: the report prints 42.35.

The steps went to the skills that own them. `debug-protocol` localised it: the amounts are already
whole numbers when `load()` returns, so the loss is inside `parse.py`, where `parse_amount` uses
`int(float(...))` and truncates. `evolve-maintain` made the one-line change. `correctness-gate`
then ran the report (42.35), reverted to see 41 again, and added a regression test, since the
existing tests never call the parser. Not touched: the summing and the printing, which were never
wrong. The release step was skipped because nothing ships.
