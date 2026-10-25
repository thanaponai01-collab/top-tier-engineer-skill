Look at `fixture/`. `python report.py data/orders.csv` is our nightly sales report; it takes
about a second and a half on last night's export. From next month the export is about ten times
bigger, and the job has a few seconds in the nightly window.

Make it fast enough for that. Finance pastes the output into the month-end pack, so not one figure
it prints may change.
