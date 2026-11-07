The structure is decent for a codebase this size. Dependencies point one way, I/O stays in two modules, and there's no dead code. The real cost is duplication, and the git history shows it repeatedly. I changed nothing and deleted the checkup's `.checkup/` scratch notes afterwards.

**What was measured:** 13 tracked files (12 of them code) and all 13 commits. Every code line was parsed. Two areas were not checked: whether things are easy to find (there's no FEATURES.md mapping features to code) and whether the tests can actually fail (that needs running them against broken code).

| Property | Verdict |
|---|---|
| Easy to find things | not checked |
| One change in one place | **poor** |
| Dependencies point one way | good (there's no `layers.txt`, so only one-way imports were checked, not which layer may import which) |
| Deep modules, narrow doors | in places |
| One way per job | **poor** |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked |

**Bugs found while reading the code (these may matter more than the structural fixes):**
- **Possible double charge:** `shop/payments.py` `charge()` retries `POST /charge` on 502/503 and on network errors with no idempotency key. If a timeout hits after the request was sent, the customer can be charged twice.
- **The receipt total isn't the amount charged:** `checkout()` charges the cart total plus sales tax, but `render()` prints `receipt_total()`, which leaves tax out.
- **Tax ignores the product:** checkout always passes the category `"general"`, so a T-shirt isn't taxed as clothing.
- **No quantity check:** `app.py` accepts `mug=-3`, which gives a negative total that is sent to `charge()`.
- **Lost emails go unnoticed:** if the order email fails, the order is still paid and nothing records the failure.
- **Smaller issues:** an unknown SKU or a missing argument crashes with a traceback. In the east region, the clothing tax rate depends on whether the amount in cents is even.

**The three things to fix first, in order:**

1. **The discount logic is copied in `shop/cart.py` and `shop/receipt.py`** (weight 9). The two files changed together in 5 commits, and three of the fixes were the copies drifting apart:
   - `716a01b`: only the cart got the new member rate.
   - `fa4e4f0`: the two files rounded differently.
   - `6c240fd`: both showed the wrong bulk percentage.

   Have one total function that both files use. The receipt should show the amount actually charged, which also fixes the missing tax. *Skill: untangle.*
2. **Two separate home-made HTTP retry loops** in payments (`http.client`) and notify (`urllib`) (weight 8). Each loop got its own bug fixes: `1fd7dcc` (connection leak), `1e77a42` (timeout) and `15edf68` (no backoff). Put retry in one place and make the payment retry safe while you're at it. *Skill: cleanup.*
3. **`legacy/tax_tables.py` `sales_tax()`** is 61 lines, nested 9 deep, with complexity 25 and no tests (weight 1). Nobody has changed it since the first commit, so it costs nothing today. It's third only because charging tax by real product category, which the shop already needs, will have to go through it. *Skill: arch-design.*

Before you rely on the tests: there are only two, and nothing has shown they would catch a broken total. The verify-loop skill can check that by running them against deliberately broken code.