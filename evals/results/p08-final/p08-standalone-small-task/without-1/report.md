I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`. The existing test, `test_total_includes_fee`, now passes. It asserts `total(10, 2) == 12`.

My first test command failed because `tests/` isn't a package, so the import path didn't resolve. I re-ran it with `PYTHONPATH=.` and got `Ran 1 test … OK`. To reproduce, run `python -m unittest discover -s tests` from `fixture/` with `PYTHONPATH=.` set.

I didn't touch the README.