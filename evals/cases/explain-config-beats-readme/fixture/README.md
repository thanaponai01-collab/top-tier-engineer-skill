# payments-worker

Takes charge jobs off the queue and charges the card through the payment gateway.
Failed charges are retried 3 times with exponential backoff, then given up on.
