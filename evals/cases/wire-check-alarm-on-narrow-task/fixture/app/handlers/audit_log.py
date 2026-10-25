import datetime

from app.bus import subscribe
from app.config import AUDIT_LOG


@subscribe("stock.changed")
def record(sku, qty, before, **_):
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {sku} {before} -> {qty}\n")
