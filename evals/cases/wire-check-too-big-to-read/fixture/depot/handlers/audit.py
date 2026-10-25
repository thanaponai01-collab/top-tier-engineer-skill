import json

from depot.bus import subscribe
from depot.store import _path


@subscribe("stock.moved")
def record(bin_id, qty, **_):
    with open(_path("audit"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"bin": bin_id, "qty": qty}) + "\n")
