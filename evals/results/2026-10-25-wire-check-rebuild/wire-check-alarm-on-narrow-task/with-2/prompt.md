Use `wire-check` on the shop CLI in `fixture/` (it is the repo root). It got a low-stock alert last
week (`app/handlers/low_stock.py`): when a sale takes a shelf under the threshold, a line should
land in `alerts.log` for the floor team. It has never written a single line. Make it work, and tell
me what was wrong.

The explicitly requested wire-check skill is at <tmp>\tte-plugin-fw4hv0gg\verify-loop\skills\wire-check\SKILL.md. Read and follow that SKILL.md before starting.

---- next session: a fresh agent, same folder ----

The shop CLI in `fixture/` (it is the repo root) has a low-stock alert now. Update README.md so the
floor team knows about it: where the alert lands and when it fires. Keep it short.
