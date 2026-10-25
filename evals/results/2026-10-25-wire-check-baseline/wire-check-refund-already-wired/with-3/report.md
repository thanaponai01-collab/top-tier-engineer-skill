The refund command is live and working, so I didn't change anything. Your teammate couldn't find it in `billing.py` because it isn't listed there by design. `billing.py` asks `registry.all_commands()` for the command list. The registry loads every module in `billing_cli/commands/` automatically, and each one adds itself with `@command("name")`. `refund.py` adds itself the same way `charge` and `balance` do. Looking for a command name in `billing.py` will never find any of them.

**How I know:** I ran the real CLI (`python billing.py ...`) in a scratch copy, so your real `balances.json` wasn't touched.

| Link | Status | Evidence |
|---|---|---|
| 1 Exists | ✅ proven | `billing_cli/commands/refund.py` loads with no errors |
| 2 Registered | ✅ proven | `@command("refund")` (`refund.py:5`); the registry loads the `commands/` folder (`registry.py:16-19`) |
| 3 Routed | ✅ proven | The usage message with no arguments lists `balance \| charge \| refund` |
| 4 Invoked | ✅ proven | `refund acme 700` → `refunded acme 700; balance 4300`, exit 0 |
| 5 Effect lands | ✅ proven | `balances.json` changed to `"acme": 4300`; `balance acme` then printed `4300`. Refunding 9999 against globex's 1200 was rejected, exit 1, and the file didn't change |

**Control check:** to show the run would catch a broken link, I deleted `refund.py` in the scratch copy. `refund` then disappeared from the command list, and calling it returned the usage message with exit 2. So the successful run above really depends on that file being loaded.

**Other things I noticed:**
- The existing test (`tests/test_charge.py`) passes, but it imports `charge()` directly, so it skips the wiring entirely. Also, `python -m unittest discover -s tests` fails because `tests/` has no `__init__.py`; running the file directly with `PYTHONPATH=.` works. Nothing tests `refund` at all.
- This isn't a wiring problem, but `refund` doesn't reject negative amounts. `refund acme -500` would pass the balance check and add 500 to the balance. You may want it to require `cents > 0`.

**Recommendation:** add a test that runs `main(["refund", "acme", "700"])` from `billing.py` against a temporary copy of `balances.json`, then checks the new balance. Do the same for every command. Tests that go through `main` exercise the registry, so a command that stops being loaded fails the test instead of passing quietly.