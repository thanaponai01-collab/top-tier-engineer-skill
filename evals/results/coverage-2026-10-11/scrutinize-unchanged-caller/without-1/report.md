**Don't merge as is.** It isn't a pure refactor, and it breaks checkout for unknown users.

**The bug is in `billing.py`.** `price_for` still relies on the old contract:

```python
try:
    tier = get_user(user_id)["tier"]
except KeyError:
    return amount_cents
```

With the PR, `get_user("nobody")` returns `None`. Then `None["tier"]` raises `TypeError`, which the `except KeyError` doesn't catch. So `price_for` crashes for any unknown or guest user, where it used to return the list price. The docstring says "anyone we can't find pays list price", so that is the behaviour that gets lost.

**The tests pass anyway because of a mock.** `tests/test_billing.py::test_guest_pays_list` patches `billing.get_user` with `side_effect=KeyError`. That simulates the old behaviour, which `get_user` no longer has. I ran the suite and it passes (4 tests OK), but it never calls the real `get_user` from `price_for`.

**What I checked:**
- I grepped for every caller of `get_user`: `profile.py` and `billing.py`. The PR updates only `profile.py`.
- The `profile.py` change is correct.
- The `users.py` change is fine in itself, but it is a public contract change (raise → return `None`), so "no behaviour change" is wrong.

**Fix before merging:**
1. Update `billing.price_for` to handle `None`:
   ```python
   user = get_user(user_id)
   if user is None:
       return amount_cents
   tier = user["tier"]
   ```
2. Change the billing test to use `return_value=None` instead of `side_effect=KeyError`. Better, add one test that goes through the real `get_user`.
3. Correct the PR description. It changes the `get_user` contract, so it isn't a pure refactor.

I haven't changed anything in the repo.