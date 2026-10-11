# Shop architecture

```mermaid
flowchart LR
  web["shop/web.py"] --> checkout["shop/checkout.py"]
  checkout --> inventory["shop/inventory.py"]
  checkout --> payments["shop/payments.py"]
  checkout --> queue["shop/jobs/queue.py"]
  queue --> worker["shop/jobs/worker.py"]
  worker --> emailer["shop/emailer.py"]
  refunds["shop/refunds.py"] --> queue
```

- Checkout reserves stock, charges the card, records the order, then puts the
  receipt email on the job queue. The customer never waits for email.
- The worker drains the queue and sends every customer email.
- Refunds use the same queue for their confirmation email.
