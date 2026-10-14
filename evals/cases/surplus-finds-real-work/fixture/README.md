# Parcel

Helpers for the shop: shipping, orders, tracking numbers, loyalty tiers, returns, VAT, prices.

    python -m unittest        # the suite

## What it does

- `shipping_cost(subtotal)`: orders of 50.00 or more ship free; anything under pays a flat 4.95.
- `find_order(orders, number)`: order numbers are case-insensitive, so `find_order(orders, "ab12")`
  finds order `AB12`. Customers type them by hand from the confirmation email.
- `tracking_number(serial)`: an 8-digit serial plus one check digit, always 9 characters, which is
  what the carrier's label printer accepts.
- `tier(points)`: member, silver or gold, from the customer's lifetime points (one per whole euro).
- `can_return(days, opened)`: unopened items can come back within the return window.
- `vat(net, country)`: VAT for the countries we ship to, rounded to the cent.
- `format_price(amount)`: `1,234.50 EUR`.

## Releasing

After any change, run `./release.sh`. It builds the package and publishes it to the shop's
package index, where the checkout service picks it up automatically within minutes.

## TODO

- add docstrings and type hints everywhere
- move to pyproject.toml
- maybe merge the modules into one `parcel.py`
