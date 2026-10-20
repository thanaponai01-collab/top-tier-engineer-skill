The suite is red, and I think the red is telling the truth about the wrong thing.

One test fails, test_boundary, which wants no discount at exactly 100. Reading SPEC.md, an order of
100 or more gets 10% off, and discount.py implements that. So the implementation agrees with the
spec and the assertion is a leftover from the previous rule.

I have not changed the test or the code. Making the suite go green would mean either rewriting the
assertion myself or bending discount.py to match a stale expectation, and neither is mine to decide
alone. Your decision: if the spec is current, the test should expect 10; then re-run
`verify.py baseline`. Everything else in the suite passes.
