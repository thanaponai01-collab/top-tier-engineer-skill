The refund command is already connected, so nothing needed fixing and I didn't change any files.

**Why your teammate couldn't find it:** `billing.py` never names any command, not even `charge` or `balance`. It calls `registry.all_commands()`, which goes through every module in `billing_cli/commands/` and imports it (`billing_cli/registry.py:15-19`). When a module is imported, its `@command("...")` decorator adds that command to the registry. `billing_cli/commands/refund.py` has `@command("refund")`, so it gets picked up the same way as the other two.

**How I know it works:** I ran it in a throwaway copy of the repo so the real `balances.json` wasn't touched:
- `python billing.py` with no arguments prints `usage: billing.py balance | charge | refund`.
- `python billing.py refund acme 300` prints `refunded acme 300; balance 4700` and exits 0.
- `python billing.py refund globex 9999` prints `cannot refund 9999: globex has only 1200 on account` and exits 1.
- The existing test suite passes on a clean copy. (My first test run failed only because I ran it in the copy where I'd already refunded acme.)

**Gaps I noticed (not blocking):**
- No tests cover refund; `tests/` only has `test_charge.py`.
- Refund doesn't reject zero or negative amounts. A negative refund raises the balance. A zero or negative refund for a customer who isn't in `balances.json` crashes with a `KeyError`.

I can add a refund test and an amount check if you'd like.