The refund command is connected and working. Nothing is broken, so I didn't change any code. Your teammate is right that `billing.py` never mentions `refund`, but it doesn't mention `charge` or `balance` either. Commands aren't listed by hand anywhere; they register themselves.

**How it connects:** `billing.py` calls `registry.all_commands()` (`billing_cli/registry.py:16`). That function scans every module in `billing_cli/commands/` and imports it. When `refund.py` is imported, its `@command("refund")` decorator adds the function to the command table. `main` then looks up `argv[0]` in that table. Reading `billing.py` alone will never show the commands.

**What I ran:** I ran the real CLI in a scratch copy of `fixture/`, so the real `balances.json` was not touched:

| Command | Result |
|---|---|
| `python billing.py` | usage lists `balance \| charge \| refund` |
| `python billing.py refund acme 300` | `refunded acme 300; balance 4700`, exit 0, and the file now holds `{"acme": 4700, ...}` |
| `python billing.py balance acme` | `4700`, so the refund was saved |
| `python billing.py refund globex 99999` | rejected with exit 1, file unchanged |
| **Check with `refund.py` removed** | usage drops to `balance \| charge` and `refund` is rejected |

The last row shows the check can tell the difference: when the file is gone, the command disappears.

| Component | Exists | Registered | Routed | Invoked | Effect lands | Evidence |
|---|---|---|---|---|---|---|
| `refund` | ✅ | ✅ module scan + `@command("refund")` | ✅ `main` looks up `argv[0]` | ✅ | ✅ `balances.json` updated | I ran it |

**Recommendation:** The one existing test, `tests/test_charge.py`, imports `charge` directly and skips the lookup step entirely, so it would still pass if command discovery broke. I'd add tests that go through `billing.main(["refund", "acme", "300"])` and `main([])` and check that the usage line lists every command. Those would catch a command being missing or failing to register. I haven't added them because you didn't ask for test changes; tell me if you want them.