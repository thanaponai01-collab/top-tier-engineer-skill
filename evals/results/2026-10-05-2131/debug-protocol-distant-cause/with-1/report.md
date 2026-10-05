The statement was short because `parse_amount` in `fixture/parse.py` dropped the cents. `python report.py` now prints `Total: 42.35`.

`debug-protocol` isn't one of my available skills, and nothing in `fixture/` defines it. I did the diagnosis directly instead. If it's a skill you expected, tell me where it lives and I'll rerun the work against it.

**Cause:** `parse_amount` was `int(float(value))`, which truncates each amount. 10.50, 20.25 and 11.60 became 10, 20 and 11, which sum to 41. The real sum is 42.35. `totals.py` and `report.py` were fine.

**Fix:** `parse_amount` now returns `Decimal(value)`, and amounts stay exact.

**Check:** I added `test_keeps_cents` to `fixture/test_totals.py`, expecting `42.35` from `data.csv`. It failed before the fix. All 3 tests pass now.

The old tests missed this because they only passed whole numbers to `total` and never went through the CSV parser.

If any other code expects `amount` to be an `int`, it will now get a `Decimal`. Nothing else in `fixture/` does.

Earlier statements printed truncated totals, so the customer's previous statements may also be short. That's a decision for you.

The Notion, Asana, Atlassian, Figma, Intercom, Linear and Slack connectors need authorizing before they can be used. For claude.ai connectors, use your claude.ai connector settings. For the others, use `/mcp` in an interactive session. I didn't need any of them here.