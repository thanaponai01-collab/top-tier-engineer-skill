Run `perf-optimize` over `fixture/`. `python report.py data/orders.csv` is our nightly sales
report; it takes about a second and a half on last night's export. From next month the export is
about ten times bigger, and the job has a few seconds in the nightly window.

Make it fast enough for that. Finance pastes the output into the month-end pack, so not one figure
it prints may change.

The explicitly requested perf-optimize skill is at <tmp>\tte-plugin-s628ugmj\verify-loop\skills\perf-optimize\SKILL.md. Read and follow that SKILL.md before starting.
