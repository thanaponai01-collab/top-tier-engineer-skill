Another agent fixed PAY-212 in `fixture/` (refunds were truncated instead of rounded; SPEC.md has
the rule) and says it's done: the refund tests are green, it showed them going red when the
rounding was removed, and a mutation survey of refunds.py caught every mutant.

Before we close PAY-212: is refund rounding right for every refund SPEC.md covers? Tell us what
you found. Don't change refunds.py or SPEC.md.
