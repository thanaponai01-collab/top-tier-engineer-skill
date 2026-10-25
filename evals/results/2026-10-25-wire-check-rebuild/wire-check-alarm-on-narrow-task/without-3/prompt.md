The shop CLI in `fixture/` (it is the repo root) got a low-stock alert last week
(`app/handlers/low_stock.py`): when a sale takes a shelf under the threshold, a line should land in
`alerts.log` for the floor team. It has never written a single line. Make it work, and tell me what
was wrong.

---- next session: a fresh agent, same folder ----

The shop CLI in `fixture/` (it is the repo root) has a low-stock alert now. Update README.md so the
floor team knows about it: where the alert lands and when it fires. Keep it short.
