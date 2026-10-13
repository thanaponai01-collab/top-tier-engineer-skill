I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`. The existing test, `test_total_includes_fee` (`total(10, 2) == 12`), now passes.

My first test command failed with an import error, which was only my discovery flags. It was not a test failure. I re-ran it with `PYTHONPATH=.` and got `Ran 1 test … OK`.

`python total.py` will now print 12 rather than 8. The README says it should print "the configured base total", which doesn't obviously match adding a fee. I left it alone since you asked for a one-line fix.