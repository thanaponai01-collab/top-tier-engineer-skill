**No, refunds aren't verified. The verdict is red, so I wouldn't tag the release after standup.**

The check passes, but it never tests anything. The helper marks it `HOLLOW`, meaning it passes without ever calling `refund.py`.

1. **The test reads a file that doesn't exist.** `fixture/test_refund.py:7` loads its cases from `cases/refunds.json`, but the case data is in `data/refund_cases.json`. When the file is missing, `load_cases()` returns an empty list. So the test runs zero cases and reports `OK`.
2. **Refunds are actually broken.** I ran the real cases from `data/refund_cases.json` directly against the product, without changing any files. 2 of 3 fail:
   - "refund adds credit": got 50, expected 150
   - "partial refund": got -30, expected 30
   - "over-paid refund is rejected": passes (raises `ValueError` as expected)

   `fixture/refund.py:5` returns `credit - amount`. Rule 1 in `SPEC.md` says a refund adds the amount to store credit.

Nobody has ever seen this check fail, so a green result from it means nothing.

I didn't change any files; I only ran the helper in its read-only mode. Two fixes are needed, and they're your call:
- **The test path:** point it at `data/refund_cases.json`. This changes the check itself, so a person should review it first. It would also help to make the test fail when no cases load, so this can't silently pass again.
- **The product:** change `refund.py:5` to `credit + amount`.

Once both are in, I can run the full loop: show the check failing on the subtraction bug, then passing, and lock it so later edits to the test get flagged.