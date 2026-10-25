The refund command is connected and working. Nothing was broken, so I didn't change any code.

**Why your teammate couldn't find it:** `billing.py` never names any command, so you won't find `charge`, `balance` or `refund` in it either. It asks `registry.all_commands()` for the list. That function (`billing_cli/registry.py:15-19`) imports every module in `billing_cli/commands/` by a name it builds at runtime (`importlib.import_module(f"{commands.__name__}.{mod.name}")`). Each module then adds itself to the list with the `@command("...")` decorator. `refund.py` uses `@command("refund")` (`billing_cli/commands/refund.py:5`) the same way `charge.py` does, so it gets picked up just like the commands that already work.

**How I know:** I ran every real way into the CLI in a throwaway copy of the repo (so your `balances.json` is untouched) and recorded which functions each run entered:

| Command | Exit | Result |
|---|---|---|
| `python billing.py` | 2 | usage line lists `balance \| charge \| refund` |
| `python billing.py charge acme 100` | 0 | charges acme |
| `python billing.py balance acme` | 0 | prints acme's balance |
| `python billing.py refund acme 300` | 0 | refunds acme and saves the new balance |
| `python billing.py refund globex 999999` | 1 | refused: "cannot refund 999999: globex has only 1200 on account" |

Those runs reached all 8 functions in the code, including `refund`. Both the success path and the overdraft refusal ran through the real command line. The wire-check gate passed all its stages and reports `WIRE-GATE: done(8 entered)`.

One gap: there's no test for refund. `tests/test_charge.py` only covers charge, and it calls the function directly, so it would also miss a command that wasn't registered. A test that runs `python billing.py refund ...` through the real entry point would catch that if the registration ever breaks.