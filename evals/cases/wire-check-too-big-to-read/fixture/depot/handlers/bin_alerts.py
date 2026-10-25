"""Tell the floor when a bin runs low and when it is emptied."""
from depot.bus import subscribe
from depot.store import _path


def _note(text):
    with open(_path("floor"), "a", encoding="utf-8") as fh:
        fh.write(text + "\n")


@subscribe("bin.low")
def on_bin_low(bin_id, qty, **_):
    _note(f"bin {bin_id} low: {qty} left")


@subscribe("bin.emptied")
def on_bin_emptied(bin_id, **_):
    _note(f"bin {bin_id} empty: schedule a refill")
