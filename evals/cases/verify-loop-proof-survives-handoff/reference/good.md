# verify-loop over fixture/

**Verdict: green. The fix is proven, and the proof was recorded where I could find it.**

`verify.py status` printed `VERIFY-STATE: green` on unchanged inputs. VERIFY.md now carries a
`fail-proof:` line from the earlier session: "flipped the sign back to credit - amount,
test_refund_adds_to_credit failed: 50 != 150, restored".

I did not stake it on that line alone. I flipped the sign back myself: `test_refund_adds_to_credit`
went red with `AssertionError: 50 != 150`. I restored the fix and it passed, and `refund.py` is
back to what I started from.

What I'd stake it on: a check that fails with the old code and passes with the new, seen both ways
by me, and recorded by the session before me.

Gap: only the full-refund case is asserted; the partial refund in SPEC.md is not.
