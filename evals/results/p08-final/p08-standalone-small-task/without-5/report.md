I changed `base - fee` to `base + fee` in `fixture/total.py`, and the existing test now passes.

`test_total_includes_fee`, which asserts `total(10, 2) == 12`, ran and passed with `PYTHONPATH=.`. My first command used `-t .` and failed with an import error, because `tests/` has no `__init__.py`. That was only a problem with how I invoked the test runner, not with the code.

I didn't run the test before the fix, so I haven't seen it fail on the old code.