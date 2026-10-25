The refund command is connected and works, so I didn't change anything. Your teammate couldn't find it in `billing.py` because commands aren't listed there by name.

**How it gets connected:**
- `billing.py` never names any command, not even `charge` or `balance`. It calls `registry.all_commands()` and dispatches on the first argument.
- `billing_cli/registry.py:15-19`: `all_commands()` uses `pkgutil.iter_modules` to import every module in `billing_cli/commands/`.
- `billing_cli/commands/refund.py:5` has `@command("refund")`. That decorator adds the function to the registry when the module is imported. `charge` and `balance` are registered the same way.

So adding a file to `commands/` is enough to make it a live command.

**How I know it works:** I ran it on a temporary copy of the fixture, so the real `balances.json` wasn't touched:
```
$ python billing.py
usage: billing.py balance | charge | refund          (exit 2)
$ python billing.py refund globex 200
refunded globex 200; balance 1000                    (exit 0)
$ python billing.py balance globex
1000
$ python billing.py refund globex 99999
cannot refund 99999: globex has only 1000 on account (exit 1)
```
`refund` appears in the usage line, reduces the balance, saves the change, and refuses to refund more than the customer has on account. It's also already in the README.

**One gap:** there are no automated tests for refund. `tests/` only has `test_charge.py`, so nothing would catch it if refund stopped working. I can add a `test_refund.py` modeled on the charge test if you'd like.