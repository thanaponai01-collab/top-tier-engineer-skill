The refund command is connected and works. Nothing was broken, so I didn't change any code.

**Why your teammate couldn't find it:** `billing.py` never names any command. It asks the registry for all commands. `billing_cli/registry.py:18` imports every module in `billing_cli/commands/` by a name it builds at runtime (`pkgutil.iter_modules` + `importlib.import_module`). When `refund.py` is imported, its `@command("refund")` decorator registers it. Reading `billing.py` alone will never show refund, or charge or balance either, because they're all wired the same way.

**How I know:** I ran the real commands through the wire-check helper in a throwaway copy, and it recorded which functions each one entered:

| Command | Exit | Result |
|---|---|---|
| `python billing.py` | 2 | usage text lists `balance \| charge \| refund` |
| `python billing.py refund acme 100` | 0 | ran `refund()` |
| `python billing.py refund acme 999999` | 1 | "cannot refund 999999: acme has only 5000 on account" |
| `charge` / `balance` / unit tests | 0 | all passed |

All 8 functions in the repo were entered by at least one command, so there's no dead code. The helper's gate check came back `WIRE-GATE: done`. I also ran it by hand in a separate temp copy: `refund acme 100` printed `refunded acme 100; balance 4900`, and `balance acme` then showed `4900`, so the change is saved to the balances file. Your real `balances.json` was not modified.

**One gap:** the only test, `tests/test_charge.py`, calls `charge()` directly. No test covers refund, and none goes through the `billing.py` → registry path. If someone renames the `@command("refund")` string, nothing will flag it. I can add a test that runs `python billing.py refund …` if you want.

The helper wrote a snapshot to `.wire/snapshot.json`. The skill suggests committing it so later checks can compare against this run.