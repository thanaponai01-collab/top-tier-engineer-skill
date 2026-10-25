The refund command is connected and working, so I didn't change anything. Your teammate couldn't find it in `billing.py` because commands aren't listed there. They're found automatically when the program runs.

**How it's wired:**

- `billing.py` never names any command. It asks the registry for the full list with `registry.all_commands()` (`billing.py:8`).
- `billing_cli/registry.py:16-19` goes through every module in `billing_cli/commands/` using `pkgutil.iter_modules` and imports each one.
- Importing `billing_cli/commands/refund.py` runs its `@command("refund")` decorator (line 5), which adds `refund` to the command table.

So any file dropped into `commands/` becomes a command, with no edit to `billing.py`. `charge` and `balance` are hooked up the same way.

**I also ran it**, on a temporary copy so the real `balances.json` wasn't touched:

```
$ python billing.py
usage: billing.py balance | charge | refund          (exit 2)
$ python billing.py refund globex 200
refunded globex 200; balance 1000                    (exit 0)
$ python billing.py refund globex 99999
cannot refund 99999: globex has only 1000 on account (exit 1)
```

The balance file was updated correctly (globex went from 1200 to 1000), and refusing to refund more than the customer has on account works. The existing test, `tests.test_charge`, passes too.

**One gap:** there's no test for refund, only `tests/test_charge.py`. A `tests/test_refund.py` covering a normal refund and an over-refund would make this clear without anyone having to trace the code. I can add it if you'd like.