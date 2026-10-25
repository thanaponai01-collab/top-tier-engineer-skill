from store import db


def run(args):
    rows = db.load()
    rows.append({"id": len(rows) + 1, "customer": args[0], "amount": float(args[1]), "paid": False})
    db.save(rows)
    print(f"order {len(rows)} added")
