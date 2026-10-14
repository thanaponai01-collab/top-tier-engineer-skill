# Pricing and orders

All money is integer cents. Wherever a percentage is applied, round half up to the cent.
Existing behaviour and tests stay as they are: in particular a `Cart()` with no region keeps
today's one-line invoice.

## 1. Bulk discount
10 or more units of the same sku: that line gets 10% off.

## 2. Coupons
`Cart.apply_coupon(code)`, applied to the subtotal after bulk discounts. The total discount never
takes the cart below zero.
- `SAVE5`: 500 off.
- `PCT10`: 10% off, at most 2000.

Any other code raises `ValueError`. A second coupon on the same cart raises `ValueError`.

## 3. Sales tax by region
`Cart(region="CA")`. Rates: CA 7.25%, NY 8.875%, OR 0%. Tax is charged on the subtotal after bulk
discounts and coupon; shipping is not taxed. A cart with no region, or an unknown one, raises
`ValueError` when its total is asked for.

## 4. Shipping (new `shop/shipping.py`)
By the cart's total weight (catalog weights are grams): up to 500 g costs 499; up to 2000 g costs
899; above that, 899 plus 150 for every started kilogram over 2000 g. Shipping is free when the
subtotal after discounts is 10000 or more. An empty cart ships for 0.

## 5. Totals and invoice
`Cart.total()` returns `{"subtotal", "discount", "tax", "shipping", "total"}`: `subtotal` is before
any discount, `discount` is bulk plus coupon, `total = subtotal - discount + tax + shipping`.
For a cart with a region, the invoice ends with five lines, in this order: `Subtotal`, `Discount`,
`Tax`, `Shipping`, `Total`.

## 6. Inventory (new `shop/inventory.py`)
Starting stock: MUG 50, TEE 30, CAP 20, PIN 200. `inventory.available(sku)` gives current stock.
`Cart.add` raises `inventory.OutOfStock` (a `ValueError`) when the cart would hold more of a sku
than is in stock.

## 7. Checkout (new `shop/orders.py`)
`orders.checkout(cart, customer=None, gift_card=None)` returns an order with `id` (`ORD-0001`,
`ORD-0002`, … in sequence), `customer`, `totals` (the dict from `Cart.total()`), `gift_card_used`
and `paid` (what is still charged after the gift card). It takes the units out of stock. An empty
cart raises `ValueError`. `orders.reset()` puts everything back to its starting state: orders and
numbering, stock, gift card balances and loyalty points.

## 8. Gift cards (new `shop/giftcards.py`)
Starting balances: `GC-100` 10000, `GC-5` 500. At checkout a gift card pays as much of the order
total as its balance allows, and its balance goes down by that much. `giftcards.balance(code)`
reads a balance. An unknown code raises `ValueError`.

## 9. Loyalty points (new `shop/loyalty.py`)
A checkout with a customer earns one point per whole 100 cents of `paid`.
`loyalty.points(customer)` reads the running total (0 for a customer never seen).

## 10. Refunds
`orders.refund(order_id, sku, qty)` returns the cents refunded and puts the units back in stock.
The refund is that line's price after bulk discount, in proportion to the units returned (half up),
plus tax at the order's rate on that amount. Coupons and shipping are not refunded. Returning more
units than were bought and not yet returned, or an unknown order, raises `ValueError`.

## 11. Order export
`orders.export_csv()` returns a header line `id,customer,subtotal,discount,tax,shipping,total,paid`
and one line per order, in order, amounts as plain integers, customer empty when there is none.
