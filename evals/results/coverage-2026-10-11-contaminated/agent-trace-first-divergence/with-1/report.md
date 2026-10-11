**Divergence: step 2.** The agent ignored the order ID in the ticket (A-1093) and ran a fuzzy `search_orders` on the name "J. Smith". The cause is a wrong tool choice. It should have called `get_order("A-1093")`, which is in `TOOLS.md`.

**Evidence** (*proven*, read from `run-4471.jsonl`):

1. **Step 1, ticket:** "Order **A-1093** … the mug … was **$50**", from `<email>`.
2. **Step 2, divergence:** The agent's reasoning is "Let me find their order." Its call is `search_orders(customer_name="J. Smith")`. The intended call was `get_order(order_id="A-1093")`.
3. **Step 3, result:** The search returned one match, A-1187, for "Jane Smith" with email `<email>`. The ticket email is `<email>`, so the customer is a different person. The order is a $500 espresso machine, not a $50 mug.
4. **Step 4:** The agent didn't notice the mismatches (order ID, email, item, price) and carried on with A-1187. It called `check_policy`, which is fine in itself and only compounds step 2.
5. **Step 5:** The policy says "refund the price of the affected item". It does not say to refund the order total.
6. **Step 6:** The agent refunded the order total of $500 instead of the item price. This is a second error, independent of the first. Even on the correct order, the policy and the ticket support $50 at most.
7. **Steps 7–8:** `issue_refund` ran with no check or confirmation, and the agent told the customer the refund was done.

**Why step 2 and not step 6:** The $500 amount appeared at step 6, but the run went wrong at step 2. After that, every step worked on the wrong order. The agent also never compared the search result with the ticket. It could have caught the mismatch at steps 3, 4 or 6, and it didn't.

**What I haven't proven:**
- Whether A-1093 exists. The trace never looks it up, so I'm assuming it does.
- Whether this is a one-off or a pattern. That needs `agent-prove` over many runs.
- Why the agent skipped the order ID. The log has no system prompt, so I can't tell whether it was told to search by name.

I haven't changed or proposed any prompt edits. Next steps are `debug-protocol` or `build-discipline` for the fix. Two candidates I noticed are a guard that checks the order against the ticket before `issue_refund`, and a cap on the amount at the item price.