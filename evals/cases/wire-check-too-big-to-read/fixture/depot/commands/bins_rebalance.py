"""Move stock from crowded bins into empty ones in the same zone."""
from depot import store


def _crowded(rows):
    return sorted((r for r in rows if r["qty"] > 15), key=lambda r: -r["qty"])


def run(args):
    rows = store.load("bins")
    empty = [r for r in rows if r["qty"] == 0]
    moved = 0
    for src in _crowded(rows):
        dst = next((e for e in empty if e["zone"] == src["zone"]), None)
        if dst:
            half = src["qty"] // 2
            src["qty"] -= half
            dst["qty"] += half
            empty.remove(dst)
            moved += 1
    store.save("bins", rows)
    print(f"rebalanced {moved} bins")
