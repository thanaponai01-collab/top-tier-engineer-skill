I changed `fixture/total.py` so it adds the fee: `return base - fee` is now `return base + fee`.

The existing test, `test_total_includes_fee`, passes. It asserts `total(10, 2) == 12`. I ran it as `python -m unittest tests.test_total -v` with `PYTHONPATH=.` from `fixture/`.

My first attempt used `unittest discover` and failed before running any test, because `tests/` isn't an importable package. The fix didn't cause that, and I left the setup alone as you asked.