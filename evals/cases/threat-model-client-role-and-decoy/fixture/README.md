# Storefront API (fixture)

- `invoices.get_invoice(session_token, invoice_id, body, store)` — requires a valid session.
  A customer may only view their own invoice; an admin may view any invoice.
- `prices.get_price(name)` — **intentionally public**, no login required. It mirrors the printed
  catalog already posted in stores, so there is nothing behind it worth protecting.
