"""Low-stock alert: tell the floor team when a shelf drops under the threshold."""
import datetime

from app.bus import subscribe
from app.config import ALERTS_LOG, LOW_STOCK_THRESHOLD


@subscribe("stock_changed")
def alert_if_low(sku, quantity, before, **_):
    if quantity < LOW_STOCK_THRESHOLD <= before:
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        with open(ALERTS_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} LOW STOCK {sku}: {quantity} left\n")
