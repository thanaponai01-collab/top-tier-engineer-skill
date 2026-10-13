I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`.

- **Test:** `test_total_includes_fee` passes (`total(10, 2) == 12`). I ran it with `PYTHONPATH=. python -m unittest tests.test_total`. My first attempt, `unittest discover -s tests`, failed with an import error because `tests` isn't a package. That was the wrong command, not a code problem.
- **Direct run:** `python total.py` now prints `12`.

I didn't use `pick-skill` to load another skill, because a known one-line fix doesn't need one.