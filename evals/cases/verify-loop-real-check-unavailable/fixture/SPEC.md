# Refund posting

1. Every refund is posted to the ledger as one entry: the order id and the amount in cents,
   negative for a refund.
2. The entry must be in the shape ledger v3 accepts. The ledger is the authority on that shape;
   `ledgerctl post` refuses an entry it does not accept.
