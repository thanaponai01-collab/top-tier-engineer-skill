# Shop rules

1. Cart: line total = quantity x unit price (cents); quantity must be at least 1.
2. Coupons: a percent coupon takes that percent off the cart, rounded down; an expired coupon
   (expiry date before today) is rejected with ValueError.
3. Gift cards: spending more than the balance is rejected with ValueError.
4. Refunds: the total refunded on an order can never exceed what was paid for it. Each refund is
   checked against what is left after earlier refunds.
