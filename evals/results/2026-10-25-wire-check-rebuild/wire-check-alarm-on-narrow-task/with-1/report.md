I added a short "Low-stock alert" section to `README.md`, but right now the alert never actually fires, so the README describes something that doesn't work yet.

**What the README now says:** when a sale takes a shelf below 5 units, a line like `2026-10-25T14:03:11 LOW STOCK sprocket: 4 left` is added to `alerts.log`. It fires once, on the sale that drops the shelf below 5. It can fire again after a restock brings the shelf back to 5 or more. The limit is `LOW_STOCK_THRESHOLD` in `app/config.py`.

**Why it doesn't fire:** the code that writes the alert is only switched on inside `restock` (`shop.py:19`). `sell` never switches it on, and a restock can't drop stock, so the alert can't go off from the command line. I checked this two ways:
- I ran `python shop.py sell sprocket 3` on a scratch copy (7 → 4). It printed `sold 3 sprocket, 4 left`, but no `alerts.log` was created.
- `tests/test_low_stock.py` fails with `low-stock alert missing from alerts.log: []`.

The same problem means sales also skip the audit trail (`audit.log`) and the restock reminder (`reorder.txt`). `FEATURES.md` still lists the alert as working, which is out of date.

The fix is one line: move `import app.handlers` to the top of `shop.py` so it runs for every command. Should I make it and rerun the tests?