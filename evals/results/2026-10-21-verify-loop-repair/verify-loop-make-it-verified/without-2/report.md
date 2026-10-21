Refunds are **not verified, so don't tag yet.** The test suite says `OK`, but it ran zero cases, and once I ran the real cases the main refund behaviour fails.

**1. The test passes without testing anything.** `test_refund.py` reads its cases from `fixture/cases/refunds.json`, which doesn't exist. The real data is in `fixture/data/refund_cases.json`. When the file is missing, `load_cases()` returns `[]` without complaint, so the one test loops over nothing and passes.

**2. Refunds take credit away instead of adding it.** I ran the three cases from `data/refund_cases.json` directly against `refund.apply_refund`:

| Case | Got | Expected |
|---|---|---|
| refund adds credit (100 credit, refund 50) | 50 | 150 |
| partial refund (0 credit, refund 30) | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError ✅ |

`fixture/refund.py:5` does `return credit - amount`. SPEC.md rule 1 says the refund is *added* to store credit, so that line should be `credit + amount`. Right now every refund lowers the customer's credit and can push it negative. Rule 2 (rejecting a refund larger than the amount paid) works.

**Fixes needed before the release:**
- In `refund.py:5`, change `-` to `+`.
- In `test_refund.py`, point `CASES` at `data/refund_cases.json`. Also make the test fail when the file is missing or empty, instead of returning `[]`, so this can't pass silently again.

I haven't changed any files. Want me to make both fixes and re-run the tests?