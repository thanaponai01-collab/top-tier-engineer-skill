# Pricing branch review

Ran `python -m unittest test_pricing.py`: 4 tests, OK. Read both agents' commits: one stabilised
the discount tests against float noise, the other added the bulk tiers from SPEC.md clause 3, with a
test for the 5% tier.

Everything passes and both pieces of work are covered by tests. It's good to go; the branch can go
out.
