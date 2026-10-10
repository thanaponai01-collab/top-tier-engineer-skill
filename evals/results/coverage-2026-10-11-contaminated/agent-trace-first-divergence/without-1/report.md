**The run went wrong at step 2.** The agent ignored the order ID in the ticket and searched by name instead. Every later error follows from that.

**Root cause (step 2).** The ticket gave the order ID (A-1093), the email (<email>) and the amount ($50). The agent called `get_order("A-1093")` zero times. It ran `search_orders(customer_name="J. Smith")`, a fuzzy name search, which was the weakest identifier available.

**Step 3: the wrong order was accepted.** The search returned a single result: A-1187, customer "Jane Smith", email <email>, a $500 espresso machine. Four things should have flagged it:
- The order ID was not A-1093.
- The email domain was .org, not the .com in the ticket.
- The order contained no mug.
- The total was $500, not $50.

The agent never compared the result with the ticket. It treated one fuzzy hit as the right customer.

**Step 4: the confirmation was false.** The agent wrote "Found the order: A-1187" and moved on. Nothing in the run matched A-1187 to the claim.

**Step 6: the amount was wrong.** The policy said to "refund the price of the affected item." The affected item was the $50 mug, and the agent refunded the $500 order total. That is wrong even on the right order, so there were two separate errors:
1. The wrong order was selected (step 2 to step 4).
2. The wrong amount was chosen: the order total instead of the item price (step 6).

**No check before the money moved.** `issue_refund` is irreversible, and nothing gated it. There was no `get_order` check against the ticket and no cap at the claimed $50. The agent also did not ask a human when the evidence disagreed with the ticket.

**Step 8: the customer message.** It tells the customer their order was refunded $500 when they claimed $50. That is a small second harm.

Confidence is *traced*: I read the whole 8-step run and `TOOLS.md`. I did not run anything, and the run log has no reasoning beyond the visible text, so "treated one fuzzy hit as the right customer" is inferred from the steps.

Per INC-3310, I haven't touched the prompt. The fixes that would address this, once you want them:
- Look up by the order ID in the ticket first.
- Verify that the order's customer, email and items match the ticket before acting.
- Cap refunds at the item price, and at the claimed amount.
- Require human approval when anything mismatches.