**Refunds are not verified: the check now fails, and I haven't changed `refund.py`.**

The original check was passing without testing anything. `test_refund.py` looked for `cases/refunds.json`, but the cases are in `data/refund_cases.json`. That meant it loaded zero cases and reported OK. I fixed the path and added an assertion that fails if no cases load. I didn't touch any expected values.

With the check actually running, 2 of the 3 cases fail (*proven*, from `python -m unittest test_refund.py`):
- **"refund adds credit":** got 50, spec says 150.
- **"partial refund":** got -30, spec says 30.

The cause is in `refund.py`. `apply_refund` returns `credit - amount`, and SPEC rule 1 says a refund adds to store credit. The fix is `credit + amount`. The over-paid rejection case passes.

I stopped at the report because you asked me to verify, not to change product code. The release shouldn't be tagged until the fix is in.

I also haven't run the full `verify.py` loop (baseline, strict run, status), so the state isn't frozen. I can make the one-character fix, rerun the check to green, and then run the rest of the loop. Do you want me to?