from depot import bus, settings, store
from depot.registry import command


def _state(qty):
    if qty == 0:
        return "empty"
    if qty < settings.LOW_STOCK:
        return "low"
    return None


@command("bins-pick")
def run(args):
    bin_id, n = int(args[0]), int(args[1])
    rows = store.load("bins")
    row = next(r for r in rows if r["id"] == bin_id)
    if n > row["qty"]:
        print(f"bin {bin_id} holds only {row['qty']}")
        return 1
    row["qty"] -= n
    store.save("bins", rows)
    bus.publish("stock.moved", bin_id=bin_id, qty=row["qty"])
    state = _state(row["qty"])
    if state:
        bus.publish(f"bin.{state}", bin_id=bin_id, qty=row["qty"])
    print(f"picked {n} from bin {bin_id}, {row['qty']} left")
