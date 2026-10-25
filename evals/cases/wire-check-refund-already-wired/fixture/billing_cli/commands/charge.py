from billing_cli import store
from billing_cli.registry import command


@command("charge")
def charge(args):
    who, cents = args[0], int(args[1])
    b = store.load()
    b[who] = b.get(who, 0) + cents
    store.save(b)
    print(f"charged {who} {cents}; balance {b[who]}")
