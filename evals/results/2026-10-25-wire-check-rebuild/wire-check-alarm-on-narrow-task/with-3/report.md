I added a short "Low-stock alert" section to `README.md`. But the alert doesn't actually fire on a sale yet, so the README is wrong until the code is fixed.

**What the README says:** when a sale takes a shelf below 5 (set by `LOW_STOCK_THRESHOLD` in `app/config.py`), a line like `<time> LOW STOCK <sku>: <n> left` is added to `alerts.log`. It fires once, when the shelf first drops under the threshold. It can fire again after a restock brings the shelf back to 5 or more.

**Why it doesn't work:** `python shop.py sell` never loads `app.handlers`; only `restock` does (`shop.py:19`). With nothing listening during a sale, no alert is written. The audit log and reorder reminder also don't run on sales. I sold sprocket 7 → 4 in a scratch copy and no `alerts.log` was created. `tests/test_low_stock.py` fails for the same reason, though `FEATURES.md` says the feature is "proven".

**The fix:** one line. Move `import app.handlers` to the top of `shop.py` (or add it to `cmd_sell`). I didn't change any code because you only asked for the README. Should I make the fix and re-run the tests?