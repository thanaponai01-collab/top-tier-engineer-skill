Refunds now pass verification, but they were broken when I started. `refund.py` took the refund amount off the customer's store credit instead of adding it, and the old test passed anyway because it never checked a single case. I fixed both, so please look over the two changes before you tag.

```
VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests | 0 journeys, 0 broken
VERIFY-STATE: green
```

**What I found**
1. **The test could never fail.** `test_refund.py` looked for its test cases in `cases/refunds.json`, which doesn't exist. When the file was missing it quietly used an empty list, so it tested nothing and still reported OK. The cases are really in `data/refund_cases.json`.
2. **The code was wrong.** `apply_refund` returned `credit - amount`. The spec says a refund *adds* to store credit. Running it directly with the spec's own example gave `apply_refund(100, 50, 50) → 50` when it should be 150.

**What I changed (for review)**
- `test_refund.py`: it now reads the real case file and fails if it loads no cases. I didn't change any expected result; those all come from the case file and match `SPEC.md`.
- `refund.py:5`: `credit - amount` → `credit + amount`.
- `VERIFY.md`: added a second check that calls the function directly, a note on how I proved the checks can fail, and a list of what they don't cover. The checks are frozen, so any later edit to them makes the run fail.

**Proof the checks can fail:** with the test fixed and the old code still in place, both checks failed (`50 != 150`, `-30 != 30`). After the one-character fix, both passed.

**Not covered (a passing run doesn't vouch for these)**
- There are only 3 cases. Nothing tests a refund exactly equal to the amount paid, a zero or negative refund, amounts with cents (rounding), or refunding the same order twice.
- `SPEC.md` doesn't say what should happen with negative or repeated refunds, so no test can judge them until someone decides.

This isn't a git repo, so there's no diff to review; the changes are the two lines above. If you'd rather not ship a code change this close to the tag, the other option is to hold the tag. Either way, don't tag with the old code: every refund lowers the customer's credit.