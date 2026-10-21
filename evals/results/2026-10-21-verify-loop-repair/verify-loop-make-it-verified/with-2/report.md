**VERDICT: green.** Refunds are verified, but only after I fixed a real bug in `refund.py`. Please review that code change before you tag the release.

**What I found:**
1. **The test never tested anything.** `test_refund.py` read `cases/refunds.json`, which doesn't exist. When the file was missing it quietly ran zero cases and passed, so a green result told you nothing. The helper flagged it as `HOLLOW` and said to repair it. It now loads the real cases file, `data/refund_cases.json`, and fails if that file is missing.
2. **That exposed a bug in the product.** `apply_refund` returned `credit - amount`, but SPEC.md §1 says a refund *adds* to store credit. The tests failed with `-30 != 30`. The fix in `refund.py:5` changes one character, to `credit + amount`.

**How it was verified:**
- **It can fail:** putting `credit - amount` back makes the test fail on `[refund adds credit]`. That's recorded as a `fail-proof:` line in `VERIFY.md`.
- **The tests are frozen**, so any later edit to them fails the run until someone reviews it.
- **Final result:** a strict run passes, and `status` prints `VERIFY-STATE: green`.
- **Mapping:** I added `path:`, `oracle:` (SPEC.md plus the cases file), `fail-signal:` and `fail-proof:` lines to the Refunds section of `VERIFY.md`.

**Limits:**
- This covers only what's mapped: the two spec rules and the three cases in `data/refund_cases.json`.
- No separate reviewer checked this. The same agent (me) repaired the test, fixed the product and froze the tests.
- `fixture/` isn't a git repository, so none of this is committed.