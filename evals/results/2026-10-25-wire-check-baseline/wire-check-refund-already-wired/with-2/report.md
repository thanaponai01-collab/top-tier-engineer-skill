Yes, refund is live and nothing is broken, so I didn't change anything. Your teammate is right that `billing.py` never mentions refund. It doesn't name any command, though, including `charge` and `balance`. Commands are found automatically at runtime.

**How it's connected (I read the whole chain, then ran it):**

1. `billing.py:8` calls `registry.all_commands()`.
2. `billing_cli/registry.py:15-19` loads every module in `billing_cli/commands/` as it runs.
3. Loading `billing_cli/commands/refund.py` runs `@command("refund")`, which adds it to `_COMMANDS`.
4. `billing.py:12` looks up `argv[0]` in that table and calls the function it finds.

So adding a file to `commands/` is the whole registration step. That's why reading `billing.py` turns up nothing.

**What I ran** (in a throwaway copy, so your real `balances.json` is unchanged):

| Command | Result |
|---|---|
| `python billing.py` | `usage: billing.py balance \| charge \| refund` |
| `python billing.py refund acme 300` | `refunded acme 300; balance 4700`, and `balances.json` showed `acme: 4700` |
| `python billing.py balance acme` | `4700`, so the refund was saved |
| `python billing.py refund globex 99999` | Refused with exit 1, balance unchanged |
| Same run with `refund.py` deleted | `refund` disappeared from the usage line |

The last row is the control: it shows that file alone controls whether the command exists.

| Link | Status | Evidence |
|---|---|---|
| 1. The file exists and loads | ✅ | ran it |
| 2. Registered (the decorator adds it) | ✅ | ran it (shown in the usage list) |
| 3. Routed (`argv[0]` → `refund`) | ✅ | ran it |
| 4. Called with real arguments | ✅ | ran it |
| 5. Its effect lands (balance saved) | ✅ | ran it (`balances.json` and `balance` both show 4700) |

**One gap worth closing:** `tests/test_charge.py` imports `charge` directly and calls it, which skips the wiring entirely. If auto-discovery broke, or someone renamed a command, every test would still pass. I'd add a test that runs a command the way a user does, through `billing.py`'s `main()`, for example `main(["refund", "acme", "300"])`, and checks the balance after. I'd also put a line at the top of `billing.py` saying commands are discovered automatically from `billing_cli/commands/`, so the next person doesn't go looking. I can add either if you want.