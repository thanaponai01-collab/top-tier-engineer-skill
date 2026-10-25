from app.bus import subscribe
from app.config import REORDER_FILE, REORDER_POINT


@subscribe("stock.changed")
def maybe_reorder(sku, qty, **_):
    if qty <= REORDER_POINT:
        with open(REORDER_FILE, "a", encoding="utf-8") as fh:
            fh.write(f"reorder {sku}\n")
