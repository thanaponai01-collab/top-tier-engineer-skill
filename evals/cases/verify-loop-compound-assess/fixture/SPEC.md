# Billing & Invoice System

## Invoice totals
1. An invoice's subtotal is the sum of line items: quantity times unit price in cents.
2. An order discount applies to the whole subtotal once, rounded half up to the nearest cent.

## Tax
1. Standard tax rate is 5% on the subtotal after discount, rounded down.
2. Orders marked exempt have 0 tax.

## Coupons
1. Promo coupons apply fixed dollar or percent discounts.
2. A coupon cannot reduce the total by more than the coupon cap (max 5000 cents).

## Shipping
1. Orders under 5000 cents pay 500 cents flat shipping.
2. Orders of 5000 cents or more get free shipping (0 cents).

## Rebates
1. Volume rebates apply retroactively for accounts exceeding monthly thresholds.
