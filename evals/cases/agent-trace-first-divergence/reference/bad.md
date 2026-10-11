# Run 4471

The agent went wrong at step 6 when it decided to refund the order total of $500.00 instead of the
item's price. The policy at step 5 clearly says to refund the affected item, so the divergence is the
refund decision: the agent misread the policy.

Fix: make the prompt say explicitly "refund only the damaged item's price, never the order total".
