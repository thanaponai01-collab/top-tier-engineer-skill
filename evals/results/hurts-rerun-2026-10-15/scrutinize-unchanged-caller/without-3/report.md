**Don't merge yet.** This isn't a pure refactor. It breaks checkout for unknown users, and the tests pass only because the billing test mocks the old behaviour.

**The bug:** `billing.py:9-12` is a second caller of `get_user` that the PR didn't update. It still relies on the old `KeyError`:

```python
try:
    tier = get_user(user_id)["tier"]
except KeyError:
    return amount_cents
```

Now that `get_user` returns `None` for an unknown user, `None["tier"]` raises a `TypeError`. The `except KeyError` doesn't catch it, so the error escapes. I ran it on both branches:

- `main`: `price_for('nobody', 1000)` returns `1000` (the guest pays list price).
- `feature/optional-user`: it fails with `TypeError: 'NoneType' object is not subscriptable`.

So any guest or unknown user reaching checkout gets an error instead of a price.

**Why the tests stay green (4/4 pass on the branch):** `tests/test_billing.py:12` patches `billing.get_user` with `side_effect=KeyError("nobody")`. That test simulates the old contract, so it can't notice that the real function changed. The PR updated `test_users.py` for the new contract but left this mock alone.

**Fixes to ask for:**
1. In `billing.py`, handle `None` the same way `profile.py` now does, e.g. `user = get_user(user_id)`, then `if user is None: return amount_cents`.
2. In `tests/test_billing.py`, change the mock to `return_value=None`. Better still, add a test that uses the real `get_user` with an unknown ID so a contract change like this gets caught next time.
3. Change the PR description. Returning `None` instead of raising changes behaviour for unknown users, so every caller of `get_user` needs checking.

The `profile.py` change is correct and behaves the same as before. The only callers of `get_user` are `profile.py` and `billing.py`, so no others are missed.