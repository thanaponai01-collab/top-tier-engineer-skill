Refunds are verified, but they weren't before. The old "passing" test was checking nothing, and the code had a real bug that would have shipped. Both are fixed, and `python -m unittest test_refund.py` in `fixture/` now passes against all 3 cases (*proven*: I ran it).

**What was wrong:**
1. **The test never tested anything.** `test_refund.py` loaded cases from `cases/refunds.json`, which doesn't exist. When the file was missing it quietly returned an empty list, so the test ran zero cases and reported OK. The real cases are in `data/refund_cases.json`. I pointed the test at that file. Now a missing file raises an error, and the test fails if no cases load, so it can't pass on nothing again.
2. **Refunds were taking money away from customers.** `refund.py` did `credit - amount`, but SPEC.md rule 1 says a refund adds to store credit. With the real cases loaded, two of them failed (`50 != 150` and `-30 != 30`). I changed the line to `credit + amount`.

**What the passing run covers:** a full refund, a partial refund, and an over-refund being rejected with `ValueError` (SPEC.md rule 2). Neither the spec nor the cases cover a zero or negative refund amount, so those aren't verified.

There's no git repo here, so nothing is committed. The changes are only in `fixture/test_refund.py` and `fixture/refund.py`. The sign bug is one someone should hear about before the tag goes out.