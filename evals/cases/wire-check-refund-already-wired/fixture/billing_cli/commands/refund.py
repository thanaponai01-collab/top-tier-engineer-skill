from billing_cli import store
from billing_cli.registry import command


@command("refund")
def refund(args):
    who, cents = args[0], int(args[1])
    b = store.load()
    if cents > b.get(who, 0):
        print(f"cannot refund {cents}: {who} has only {b.get(who, 0)} on account")
        return 1
    b[who] -= cents
    store.save(b)
    print(f"refunded {who} {cents}; balance {b[who]}")
