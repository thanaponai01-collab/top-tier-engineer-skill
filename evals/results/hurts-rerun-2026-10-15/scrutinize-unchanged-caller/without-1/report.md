**Don't merge yet.** This isn't a pure refactor. It changes how `get_user` behaves, and it breaks a caller the PR doesn't touch.

**The bug is in `billing.py`.** `price_for` (`billing.py:9-12`) still expects the old behaviour:

```python
try:
    tier = get_user(user_id)["tier"]
except KeyError:
    return amount_cents
```

`get_user` now returns `None` for an unknown user instead of raising `KeyError`. So `None["tier"]` raises a `TypeError`, which the `except KeyError` doesn't catch. On the branch, I ran this:

```
>>> price_for('nobody', 1000)
TypeError: 'NoneType' object is not subscriptable
```

On `main`, the same call returns `1000` (list price). After this change, checkout crashes for any user ID that isn't in the user store.

**Why the tests still pass:** I ran them on the branch and all 4 pass. The PR's claim is accurate, but it doesn't show the change is safe. `tests/test_billing.py:12` replaces `get_user` with a stub that raises `KeyError("nobody")`, so the billing test checks the old behaviour, not the real function. The PR updated the tests for `get_user` itself but missed this stub.

**What's fine:**
- The change to `users.py` is correct for what it's trying to do.
- `profile.py` was updated correctly.
- The test in `test_users.py` matches the new behaviour.
- Known users behave exactly as before.

**Fixes to ask for before merging:**
1. In `billing.py`, replace the try/except with `user = get_user(user_id)` and `if user is None: return amount_cents`. That's the same pattern `profile.py` now uses.
2. In `tests/test_billing.py`, change the unknown-user stub to `return_value=None`, or better, test against the real `get_user` so this kind of change can't slip through again.
3. Reword the PR: it changes the API, so "pure refactor" is wrong. Any code outside this repo that catches `KeyError` from `get_user` will break the same way.

Smaller point: `profile.py` uses `if user`, which also treats an empty dict as missing. That's harmless here, but `is None` would be more precise.

I didn't change anything in the repo. The branch is checked out as before, and I deleted the `__pycache__` folders the test run created.