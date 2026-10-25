Yes, the refund command is connected and works. Your teammate didn't find it in `billing.py` because commands are never listed there; they register themselves. Nothing is broken, so I made no changes.

**How it's wired:**
- `billing.py` has no hard-coded command names. It calls `registry.all_commands()` and dispatches on `argv[0]`.
- `billing_cli/registry.py:15-19` (`all_commands()`) uses `pkgutil.iter_modules` to import every module in `billing_cli/commands/`.
- Each module registers itself with a decorator. `billing_cli/commands/refund.py:5` has `@command("refund")`, the same way `charge.py` and `balance.py` do.

So adding `refund.py` to that folder is enough to make it live.

**How I know it runs:** I ran it on a temporary copy of the fixture, so your real `balances.json` is unchanged.

```
$ python billing.py
usage: billing.py balance | charge | refund        (exit 2)
$ python billing.py refund acme 300
refunded acme 300; balance 4700                    (exit 0)
$ python billing.py refund globex 99999
cannot refund 99999: globex has only 1200 on account   (exit 1)
$ python billing.py balance acme
4700
```

`refund` shows up in the usage line, takes the amount off the balance and saves it, and refuses to refund more than the customer has on account. The existing `tests/test_charge.py` also passes.

**Worth knowing:** there are no tests for `refund`; the only test covers `charge`. Adding a refund test, including the over-refund case, would make it obvious next time that the command is live.