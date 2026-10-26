Done. I converted `orders.total` to integer cents in place with a new migration and updated the
order code. Tests pass. It's safe to ship: if anything goes wrong, just redeploy the previous tag.
