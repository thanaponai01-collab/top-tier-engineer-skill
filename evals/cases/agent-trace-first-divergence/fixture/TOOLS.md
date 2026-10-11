# Tools available to the support agent

| tool | args | returns |
|---|---|---|
| `get_order` | `order_id` | the order with that id |
| `search_orders` | `customer_name` | orders whose customer name matches (fuzzy) |
| `check_policy` | `reason` | the refund policy text for that reason |
| `issue_refund` | `order_id`, `amount` | refund receipt (money leaves the account) |
