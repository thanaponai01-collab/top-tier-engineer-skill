# Billing rules

All amounts are integer cents.

1. Seat prices per month: starter 900, team 2900, business 7900. Unknown plans and fewer than one
   seat are rejected with ValueError.
2. Volume discount on the seat price: 10 or more seats 5% off, 20 or more 10% off, 50 or more
   15% off. Discounted prices round down to the cent.
3. Monthly amount = seat price x seats. Annual billing charges 10 months for 12.
4. Proration: amount x days used / days in period, rounded half up. Days used outside
   0..days in period is a ValueError.
5. Account credit pays as much of an invoice as it can; the rest of the credit carries over.
6. A total split across N cards: parts differ by at most one cent, the first parts carry the
   extra cents, and the parts always add up to the total.
7. Late interest: none within a 7-day grace period; after it, 0.1% of the amount per day late
   past the grace period, rounded down.
