I fixed the bug in `fixture/total.py`: `total` now returns `base + fee` instead of `base - fee`.

I read pick-skill and decided no skill fit. This was a one-line fix with a known cause, so I did it directly.

- **Test:** `tests/test_total.py` passes (1 test, OK).
- **Direct check:** `python total.py` now prints `12`; before the fix it would have printed `8`.

My first test run used `unittest discover`, which failed because `tests/` has no `__init__.py`. That was a problem with how I ran it, not with the code. I ran the test file directly with `PYTHONPATH=.` instead.