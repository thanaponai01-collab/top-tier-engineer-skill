# Architecture review

Per `docs/architecture.md`, checkout already sends receipts through the job
queue, so the design is sound. The flow is: web → checkout → inventory,
payments → queue → worker → emailer.

The main issue I see is in `shop/checkout.py`: emails are sent during checkout,
which slows it down. Move the receipt email to the background queue.

Next steps:
1. Move `send_receipt` to the queue.
2. Add tests.
