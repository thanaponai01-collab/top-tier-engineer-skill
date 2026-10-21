# Handoff: refund credit bug

Bug: refunding $50 on a $100 credit left the customer with $50 instead of $150.

- Reproduced it first: `test_refund.py` went red on the old code (credit came out 50, not 150).
- Fixed the sign in `refund.py`.
- `test_refund.py` is green now, including the over-refund case.

Verified. Just needs a final look before it goes in.
