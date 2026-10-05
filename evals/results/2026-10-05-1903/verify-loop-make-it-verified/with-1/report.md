Refunds now verify: `run --strict` passes and `status` prints `VERIFY-STATE: green`. That covers only the three cases in the data file, and spec item 2 has just the one over-paid case, with no boundary case. This is proven by running it.

Two things were wrong, and neither showed up before:

- **The check was empty.** `test_refund.py` looked for `cases/refunds.json`, but the data lives in `data/refund_cases.json`. It loaded zero cases and passed regardless of what the code did. I fixed the path in `fixture/test_refund.py` and left the expected values alone.
- **Refunds subtracted credit.** `refund.py` returned `credit - amount`, but spec item 1 says a refund adds to store credit. I changed it to `credit + amount`.

After the path fix the check went red with specific failures (`50 != 150`, `-30 != 30`). I froze the baseline at that point, applied the product fix, and it went green. `verify.py tests --strict` shows 1 test mapped to the feature, with no skipped tests and none that can't fail.

**For review:** the check files I changed are `test_refund.py` (path only) and `VERIFY.md` (added `oracle:`, `fail-signal:`, `fail-proof:` and a blind-spots note).

**Gaps:** there are no boundary cases for `amount == paid` or negative amounts. Adding them would mean re-baselining.

I couldn't use a git revert for the "prove it can fail" step because the directory isn't a repo. The red state was the original bug itself.