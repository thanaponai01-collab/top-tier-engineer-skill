Yes, refund is connected. Nothing is broken, so I didn't change any code.

**Why your teammate couldn't find it:** `billing.py` never names any command. Not `charge`, not `balance`, not `refund`. It calls `registry.all_commands()`, which loads every module in `billing_cli/commands/` at runtime (`billing_cli/registry.py:18`). Each module adds itself to the command table with the `@command("…")` decorator. `refund.py` has `@command("refund")` (`billing_cli/commands/refund.py:5`), so it's picked up the same way the other two commands are. Searching billing.py for "refund" will always come up empty, and that's expected with this design.

**How I know it works:** I didn't just read the code. The `wire-check` helper ran every way into the CLI in a throwaway copy of the repo and recorded which functions each command actually entered:

| Command | Exit | Result |
|---|---|---|
| `python billing.py` | 2 | usage lists `balance \| charge \| refund` |
| `python billing.py charge acme 100` | 0 | ran |
| `python billing.py balance acme` | 0 | ran |
| `python billing.py refund acme 300` | 0 | went through `main` → registry → `refund` → `store.load`/`store.save` |
| `python billing.py refund globex 99999` | 1 | `cannot refund 99999: globex has only 1200 on account` (the overdraft check works) |
| `python -m unittest discover -s tests` | 0 | passed |

All 8 functions in the repo were entered by a real command, so there's no dead code. The gate's final result was `WIRE-GATE: done(8 entered)`.

**Small gap:** `tests/test_charge.py` only tests `charge`, so no test covers refund. If someone removed the `@command("refund")` line, the suite would still pass. I can add a refund test if you want one.

The helper saved its snapshot in `fixture/.wire/`. The skill says to commit that with changes, but this directory isn't a git repo, so I left it uncommitted.