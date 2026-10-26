# shop

A small shop: `app/` is the web app's order code, `worker/` the nightly invoice run, `migrate.py`
the schema migrations. Both read `data/shop.db` (set `SHOP_DB` to point them at another file).

    python -m unittest discover tests
    python -m worker.invoices 2026-10-20

See DEPLOY.md for how releases go out.
