# PAY-212 — not done

**VERDICT: red.** The tests are green, the recorded red run is real, and the mutation survey did
score 10/10. Refund rounding is still wrong for most of the percentages SPEC.md covers.

refunds.py rounds half up only when `pct % 5 == 0`. For any other percentage it still truncates:
`refund_cents(999, 33)` is 329.67 cents, which SPEC.md rounds to 330, and the code returns 329,
a cent short. The same happens at 7%, 12%, 33% and so on: about 80% of valid percentages.

Why every check passed: every test case uses a percentage that is a multiple of 5 (15, 10, 50, 25,
5, 100). The red/green proof and the mutation survey both run against those same six inputs, so
they prove the code handles them, not the rule. I added `fresh: 5` to the Refunds feature with a
seeded test that draws random prices and percentages and computes the expected value from the
spec's formula. `verify.py run` reports OVERFIT on the first seed.

Don't close PAY-212. Remove the `pct % 5 == 0` condition in refunds.py and keep the seeded check.
I did not change refunds.py or SPEC.md.
