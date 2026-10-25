Everything reachable from cli.py is used. Not reached from it: reports/weekly.py, jobs/compact_outbox.py,
notify/receipt.py's send, store/outbox.py, pricing/coupons.py, integrations/, and admin_tools/.
admin_tools is unused and integrations are dead, so delete them along with the weekly report.
