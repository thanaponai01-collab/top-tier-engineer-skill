"""Posts paid orders to the #sales channel. Enabled per deployment: LEDGER_PLUGINS=slack_hook."""


def install(commands):
    original = commands["checkout"]

    def checkout_and_post(args):
        result = original(args)
        print(f"[slack] order {args[0]} paid")
        return result

    commands["checkout"] = checkout_and_post
