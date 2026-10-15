**Don't merge it yet.** It's not a pure refactor: the branch breaks checkout for unknown users, and the passing tests don't catch it.

**The bug:** `get_user` no longer raises `KeyError` for a missing user; it returns `None`. `profile.py` was updated to handle that, but `billing.py` wasn't. It still expects the old behaviour:

```python
# billing.py:9-12
try:
    tier = get_user(user_id)["tier"]
except KeyError:
    return amount_cents
```

Now `get_user` returns `None`, and `None["tier"]` raises `TypeError`, which this `except KeyError` doesn't catch. I ran it on the branch:

```
$ python -c "import billing; print(billing.price_for('nobody', 1000))"
TypeError: 'NoneType' object is not subscriptable
```

On `main` the same call returns `1000` (an unknown user pays list price, as the docstring says). On this branch, any guest or unknown user who reaches checkout crashes it.

**Why the tests still pass:** `tests/test_billing.py:12` mocks `get_user` with `side_effect=KeyError("nobody")`, so the billing test still sees the old behaviour. All 4 tests pass (I ran them), but the guest test never calls the real `get_user`. The "tests are green" claim is true, but it doesn't show the change is safe.

**Fixes the branch needs:**
1. In `billing.price_for`, replace the try/except with a `None` check, e.g. `user = get_user(user_id)`, then `if user is None: return amount_cents`.
2. Change the mock in `test_billing.py` to `return_value=None` so it matches the new contract. Better still, add one billing test that uses the real `get_user` with an unknown ID, so this kind of mismatch fails a test next time.
3. Change the PR description: it changes behaviour for every caller of `get_user`, not just known users. Any code outside this repo that catches `KeyError` from it will break the same way.

**Minor:** `profile.py` uses `if user`, so an empty dict would also show "Guest". `if user is not None` says what's meant. This doesn't matter with the current data.

`users.py`, `profile.py` and the `test_users.py` changes all look correct. `billing.py` is the only caller that was missed; `profile.py` and `billing.py` are the only callers in the repo.