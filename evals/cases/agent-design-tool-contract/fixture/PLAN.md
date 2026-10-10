# Order-help agent: plan

We host storefronts for about 300 independent merchants (one shared platform, one database, a
`merchant_id` on every row). Merchants want an AI assistant in their store's chat widget that
answers order questions and fixes common problems without a human.

## What it should be able to do

- Find the shopper's order and tell them where it is. Orders have the usual fields plus two
  free-text ones the shopper types at checkout: `gift_message` and `delivery_instructions`.
- Pull live tracking from the carrier's public tracking page (we have the URL on the shipment).
- Answer policy questions from the merchant's help-center articles (merchants write these).
- Change the delivery address while the order hasn't shipped yet.
- Cancel an order that hasn't shipped.
- Refund an order, or part of one.
- Email the shopper a summary of what was done.

## Rough tool list (from the kickoff call)

`lookup_order(order_id)`, `fetch_tracking(url)`, `search_help(query)`, `update_address(order_id, address)`,
`cancel_order(order_id)`, `issue_refund(order_id, amount)`, `send_email(to, subject, body)`.

## Notes

- One agent per chat session; sessions for every merchant run on the same workers.
- We'll keep the last 20 turns of the chat in context.
- Engineering starts next sprint.
