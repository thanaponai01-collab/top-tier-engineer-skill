from billing_cli import store
from billing_cli.registry import command


@command("balance")
def balance(args):
    print(store.load().get(args[0], 0))
