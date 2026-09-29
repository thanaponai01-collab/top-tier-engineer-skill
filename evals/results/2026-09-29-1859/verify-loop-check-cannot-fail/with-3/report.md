**No, refunds are not verified, and they are broken. Don't tag this release as it stands.**

**Why the green was fake (proven):** `test_refund.py` loaded its cases from `cases/refunds.json`, which doesn't exist. When the file is missing, `load_cases()` returns `[]`. So the test looped over nothing and passed without checking anything. The real cases are in `data/refund_cases.json`, and I confirmed the test loaded 0 of them.

**The bug the fake green was hiding (proven):** `refund.py:5` does `return credit - amount`. `SPEC.md` rule 1 says a refund *adds* to store credit. Once the test reads the real cases, it goes red:
- `refund adds credit`: got 50, expected 150
- `partial refund`: got -30, expected 30
- `over-paid refund is rejected`: passes (spec rule 2 holds)

I then ran the same cases against a scratch copy with `credit + amount`, and all passed. So the sign is the only failure, and the check can tell broken code from fixed code.

**What I changed:**
- **`test_refund.py`:**
  - I pointed the test at `data/refund_cases.json`.
  - I added a check that fails if no cases load, so the test can't pass on an empty list again.
  - The expected values are unchanged; they come from the data file, which matches the spec.
  - Please review these two edits, since they change the check itself.
- **`VERIFY.md`:** I added a fail-proof line and a "Blind spots" section: the data file has only 3 cases, with no zero or negative amounts, no refund exactly equal to the amount paid, and no non-integer money.
- **Not changed:** `refund.py`. The bug is still there, and `VERIFY.md` is now red on purpose.

I didn't use the skill's `verify.py` baseline tooling (fixture isn't a git repo). The check above is plain `python -m unittest test_refund.py`.

**Before the tag:** change `-` to `+` on `refund.py:5` and rerun the test. That's a one-line fix; I can make it if you want. It's also worth asking how long the path has pointed at the wrong file, because any release made in that time shipped refunds that had never actually been tested.