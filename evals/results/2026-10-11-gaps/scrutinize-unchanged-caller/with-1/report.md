**Don't merge as-is (fix first).** This changes behaviour, so it isn't a pure refactor. It breaks checkout for unknown users in a file the PR doesn't touch. The tests pass only because they mock the part that broke.

**What I reviewed:** `git diff main...feature/optional-user` in `fixture/` (commit `ec6fc35` against `main`). It changes `users.py`, `profile.py` and `tests/test_users.py`, and adds `PR.md`. I also read all of `billing.py` and `tests/test_billing.py`. I tried to make a separate scratch checkout, but it failed because `fixture/` already has this branch checked out. So I ran things in `fixture/` itself without changing any files, and deleted the `__pycache__` folders the runs created.

**Should it exist?** Yes. Returning `None` instead of raising `KeyError` is a reasonable API change. But it changes what `get_user` promises every caller, so each caller has to be updated. The PR updated one of the two.

### Blocker
**`billing.py:9-12`: checkout crashes for unknown users.** `price_for` still expects the old `KeyError`:
```python
try:
    tier = get_user(user_id)["tier"]
except KeyError:
    return amount_cents
```
Now `get_user` returns `None`, so `None["tier"]` raises a `TypeError`. The `except KeyError` doesn't catch it. Before this change, a guest paid the full price. Now checkout throws an error.
- **Proven:** on this branch, `billing.price_for('nobody', 1000)` raises `TypeError: 'NoneType' object is not subscriptable`.
- **Smallest fix:**
  ```python
  user = get_user(user_id)
  if user is None:
      return amount_cents
  tier = user["tier"]
  ```

### Major
**`tests/test_billing.py:12`: the guest-pricing test mocks around the bug.** It patches `billing.get_user` to raise `KeyError`, which is the old contract. That's why "tests are green" (proven: 4 tests, OK) while the real code crashes. Change the mock to `return_value=None`, or better, drop the mock and use the real `get_user("nobody")`. Either version fails on the current branch and passes once the fix above is in.

### Minor
- **`profile.py:7`:** `if user` treats any falsy user as a guest. Use `if user is not None` to be precise. It doesn't matter for the current data. I checked the profile path and it works: `display_name('nobody')` gives `Guest`, and `display_name('u1')` gives `Ada`.
- **`PR.md`:** it says "no behaviour change", but the function's contract changed. Say so, and list the callers that were updated.

**Checked and fine:** the `users.py` change itself, `profile.py`, and `tests/test_users.py`. `billing.py` is the only other caller of `get_user` in the repo.