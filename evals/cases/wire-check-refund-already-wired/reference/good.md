It is connected, and it works. billing.py never names commands: it asks `registry.all_commands()`,
which loads every module in billing_cli/commands/ with `pkgutil.iter_modules`; loading
refund.py runs `@command("refund")`, which registers it.

Proven: `python billing.py` lists `balance | charge | refund` in its usage line;
`python billing.py refund globex 200` took globex from 1200 to 1000, and refunding more than the
balance is refused. Nothing changed in the code.
