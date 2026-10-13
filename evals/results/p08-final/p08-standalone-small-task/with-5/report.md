I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`.

I read `pick-skill` first. The cause was already known and the fix is one line, so no skill would have added anything and I made the fix directly.

I ran the test and the script:
- **Test:** `tests.test_total` passes, with `total(10, 2) == 12`. I ran it with `PYTHONPATH=.`.
- **Script:** `python total.py` now prints `12`.

One of my first commands, `unittest discover -s tests`, failed. It failed with "Start directory is not importable" because `tests/` has no `__init__.py`. That is a test-layout problem, not part of this fix, and I left it alone.