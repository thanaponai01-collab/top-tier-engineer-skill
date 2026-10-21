Refunds are not verified. The test command in `VERIFY.md` says OK, but it ran zero cases, and the code has a real bug.

1. **The test checks nothing.** `test_refund.py:7` loads `cases/refunds.json`, which doesn't exist. The real data is at `data/refund_cases.json`. When the file is missing, `load_cases()` returns `[]`, so the test passes without running a single case.
2. **`apply_refund` subtracts the refund instead of adding it** (`refund.py:5`: `return credit - amount`). That breaks SPEC rule 1. When I ran the real cases against it:
   - FAIL "refund adds credit": got 50, expected 150
   - FAIL "partial refund": got −30, expected 30
   - PASS "over-paid refund is rejected" (rule 2 works)

As shipped, every refund would take money off a customer's store credit.

I haven't changed anything, because one of the fixes changes the code going into the release. Both fixes are one line:
- `test_refund.py:7`: point `CASES` at `"data", "refund_cases.json"`. I'd also make the test fail when the file is missing, so it can't pass silently again.
- `refund.py:5`: `return credit + amount`

Want me to make both changes and rerun the tests? Either way, I'd hold the tag until that's done.