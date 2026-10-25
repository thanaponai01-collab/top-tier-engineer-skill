# shop

A tiny stock-keeping CLI.

    python shop.py stock               # show stock levels
    python shop.py sell <sku> <n>      # take n off the shelf
    python shop.py restock <sku> <n>   # put n back

Stock lives in `inventory.json`. Every stock change goes out on the event bus (`app/bus.py`); the
handlers in `app/handlers/` react to it (the audit trail in `audit.log`, the restock reminder in
`reorder.txt`).
