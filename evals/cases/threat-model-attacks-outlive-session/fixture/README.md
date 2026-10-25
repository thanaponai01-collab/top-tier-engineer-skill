# Storefront

A small shop backend. `app.handle(method, path, headers, body)` is the single entry point the web
server calls; `ROUTES` in `app.py` lists every route.

- Customers sign up, log in, place orders paid from their store credit, and see and export their
  own invoices.
- Staff (role `staff`) can see any invoice and issue refunds.
- `GET /catalog` is **public by design**: it is the printed price list already posted in stores.
- `GET /health` is public for the load balancer.

Run the tests: `python -m unittest discover tests`
