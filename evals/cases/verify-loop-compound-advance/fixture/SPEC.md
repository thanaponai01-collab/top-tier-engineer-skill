# Settlement & Payout Specification

## Payout subtotal
1. Payout subtotal is the sum of all item amounts in cents.
2. The net payout is the subtotal minus processing fee in cents.
3. If the fee exceeds the subtotal, the net payout is 0 (cannot be negative).

## Processing fees
1. Standard transactions (amounts <= 100000 cents) incur a 1% fee, rounded down.
2. High-volume transactions (amounts > 100000 cents) incur a 2% fee, rounded down.
