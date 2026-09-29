The refunds don't pass verification, so don't tag yet. The documented check comes back green, but it doesn't test anything. When I ran the real cases, the code subtracts refunds from store credit when it should add them.

**1. The test checks nothing.** `test_refund.py` loads `cases/refunds.json`, which doesn't exist. `load_cases()` returns `[]` when the file is missing, so the loop never runs. `python -m unittest -v test_refund.py` printed `Ran 1 test ... OK` with no cases checked. The real cases are in `data/refund_cases.json`.

**2. The refund logic breaks rule 1 of the spec.** I ran all three cases from `data/refund_cases.json` directly against `refund.apply_refund`:

| Case | Got | Expected |
|---|---|---|
| refund adds credit (100 credit, 50 refunded) | 50 | 150 ❌ |
| partial refund (0 credit, 30 refunded) | -30 | 30 ❌ |
| refund larger than amount paid is rejected | ValueError | ValueError ✅ |

`SPEC.md` rule 1 says a refund *adds* to store credit, but `refund.py:5` does `return credit - amount`. Every refund lowers the customer's credit, and it can go negative. Rule 2 (rejecting refunds larger than the amount paid) works.

I haven't changed anything, because changing how money is calculated right before a release should be your call. The fix is two lines:
- `refund.py:5`: change `credit - amount` to `credit + amount`
- `test_refund.py:7`: change `"cases", "refunds.json"` to `"data", "refund_cases.json"`

I'd also make `load_cases()` fail when the file is missing instead of returning `[]`, so the test can't pass on nothing again.

Want me to apply these and re-run the check? It should then run all three cases and pass.