**Verdict: fix-then-ship.** The branch breaks checkout for unknown users, and the PR's "pure refactor" claim is wrong.

**Reviewed:** `git diff main...feature/optional-user`. The merge base is `e805e50`, and the branch adds one commit. The goal is to make `get_user` return `None` instead of raising `KeyError`. I weighed one cheaper option: keep `get_user` as it was and add a separate `find_user` that returns `None`. That would break nothing.

**Blocker: `billing.py:10` still expects `KeyError`** (proven)
- `price_for` does `get_user(user_id)["tier"]` inside `try/except KeyError`, and the PR doesn't touch it.
- The docstring says "anyone we can't find pays list price", but that no longer holds.
- Unknown users now hit `None["tier"]`, which raises `TypeError`. The `except KeyError` doesn't catch it, so checkout crashes.
- I ran `price_for('nobody', 1000)` on the branch and got `TypeError: 'NoneType' object is not subscriptable`. On main it returns 1000.
- A search of the repo found only two callers, `profile.py` and `billing.py`. The author updated one and missed the other.

**Major: the tests can't catch this** (proven)
- `tests/test_billing.py:12` mocks `billing.get_user` with `side_effect=KeyError`, so it never exercises the real `get_user`.
- The suite passes, 4 of 4, while the real path is broken.

**Minor**
- "Pure refactor, no behaviour change" is inaccurate. The contract of a public function changed, and one caller's behaviour changed with it.
- Any caller outside this repo that catches `KeyError` would break the same way. I can't see those from here.

**Smallest fix**
1. In `billing.py`, replace the `try/except` with `user = get_user(user_id)`, then `if user is None: return amount_cents`.
2. Change the billing test to mock `return_value=None`, or better, call the real `get_user("nobody")`.
3. Or take the cheaper alternative above and leave `get_user` alone.

I didn't change any files.