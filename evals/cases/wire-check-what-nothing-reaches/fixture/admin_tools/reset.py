from store import db


def run(args):
    if "--yes" not in args:
        print("this wipes every order; pass --yes")
        return 1
    db.save([])
    print("ledger reset")
