from store import db


def run(args):
    rows = db.load()
    for i, r in enumerate(rows, 1):
        r["id"] = i
    db.save(rows)
    print(f"{len(rows)} orders renumbered")
