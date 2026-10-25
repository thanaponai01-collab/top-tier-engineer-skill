from depot import bus, store
from depot.registry import command


def _parse_line(line):
    sku, qty = line.split(":")
    return sku.strip(), int(qty)


def _parse_legacy_asn(blob):
    """Old supplier ASN format (fixed width), from before the EDI switch."""
    return [(blob[i:i + 8].strip(), int(blob[i + 8:i + 12])) for i in range(0, len(blob), 12)]


@command("inbound-receive")
def run(args):
    bin_id = int(args[0])
    rows = store.load("bins")
    row = next(r for r in rows if r["id"] == bin_id)
    for line in args[1:]:
        _sku, qty = _parse_line(line)
        row["qty"] += qty
    store.save("bins", rows)
    bus.publish("stock.moved", bin_id=bin_id, qty=row["qty"])
    print(f"bin {bin_id} now {row['qty']}")
