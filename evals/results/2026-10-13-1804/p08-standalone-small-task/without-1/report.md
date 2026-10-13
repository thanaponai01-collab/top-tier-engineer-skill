I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`. The existing test, `test_total_includes_fee`, now passes: `total(10, 2)` gives 12.

I ran it from inside `fixture/` with `PYTHONPATH=.` and `python -m unittest tests.test_total -v`. My first attempts ran from the parent directory and failed to find `tests`. That was only a path problem, not a code problem.