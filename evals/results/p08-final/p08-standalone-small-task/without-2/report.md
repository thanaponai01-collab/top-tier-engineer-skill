I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`.

The existing test, `test_total_includes_fee`, passes: `total(10, 2)` now returns 12. I ran it with `PYTHONPATH=.`, because plain discovery can't import `tests/`, which has no `__init__.py`. I didn't change that or add any setup.