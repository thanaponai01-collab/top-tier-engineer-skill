from store import db


def run(args):
    for r in db.load():
        print(f"{r['id']:>4} {r['customer']:12} {r['amount']:>9.2f} {'paid' if r['paid'] else 'open'}")
