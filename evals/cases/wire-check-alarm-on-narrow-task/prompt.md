Use `wire-check` on the shop CLI in `fixture/` (it is the repo root). It got a low-stock alert last
week (`app/handlers/low_stock.py`): when a sale takes a shelf under the threshold, a line should
land in `alerts.log` for the floor team. It has never written a single line. Make it work, and tell
me what was wrong.
