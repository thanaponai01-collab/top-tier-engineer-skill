# shop

Small order-management CLI. Data lives in `data/orders.json`.

```
python shop.py list                 # one line per order
python shop.py show A-1001          # an order and its lines
python shop.py dashboard            # top orders and customers by value
python shop.py refund A-1001 L2     # refund one line, print a receipt
python shop.py backup backup.json   # write every order to a backup file
python shop.py restore backup.json  # replace data/orders.json from a backup
```

Amounts are integer cents. Run the tests with `python -m unittest discover tests`.
