# Checkup: shop

Measured: 13 tracked files, 12 of them code, 13 commits of history. Tests that can fail and the
feature map were not checked.

Two bugs came up while reading the code, and they come before any structure work:

- `shop/receipt.py` receipt_total prints the discounted subtotal without tax, while
  `shop/checkout.py` charges cart total plus sales tax: the receipt shows a different amount
  from what the customer was charged.
- `shop/payments.py` charge retries `POST /charge` on timeouts and 502/503 with no idempotency
  key, so one order can be charged more than once.

Overall the structure is fine in places: most modules are small and do one job. Fix first:

1. **The discount rule lives in two places.** `shop/cart.py` and `shop/receipt.py` each hold
   their own copy of the member and bulk discount, with no import between them. They changed
   together in 5 commits, and the fixes show them drifting: "fix: receipt total differs from cart
   for members", "fix: receipt and cart round the discount differently". Move the rule to one
   function both call.
2. **HTTP is done two ways.** `shop/notify.py` uses urllib.request and `shop/payments.py` uses
   http.client, each with its own retry and timeout loop, and each got its own fixes (email
   timeouts, leaked connections). One shared client would take those fixes once.
3. **`legacy/tax_tables.py`** is the most tangled function (sales_tax nests nine deep), but nothing
   has changed it since the first commit. Leave it alone until a tax change is planned.
