import os

DATA_DIR = os.environ.get("LEDGER_DATA", "data")
COUPONS_ENABLED = False          # pricing review pending, see #212
PLUGINS = [p for p in os.environ.get("LEDGER_PLUGINS", "").split(",") if p]
