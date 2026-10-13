I changed `fixture/total.py` so the fee is added to the base (`base + fee`, was `base - fee`). The test passes and `python total.py` prints `12`.

I used pick-skill and it pointed to no skill for this, since the cause was known and the fix was one line. I made the change directly.

The test run that passed was `python -m unittest discover -s tests` with `PYTHONPATH` set to `fixture`. The first attempt, without `-t .` working, failed with an import error because `tests` isn't a package. That error was in how I called the test runner, not in the code.