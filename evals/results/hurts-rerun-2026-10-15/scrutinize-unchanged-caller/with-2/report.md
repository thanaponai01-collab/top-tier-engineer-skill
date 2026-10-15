## Verdict: fix before merging

This isn't a pure refactor. It breaks checkout for unknown users. `get_user` now returns `None` for an unknown user instead of raising `KeyError`, but `billing.py` wasn't updated and still expects `KeyError`. So `price_for("nobody", …)` used to return list price and now crashes with a `TypeError`. The tests pass anyway because the billing test fakes `get_user` and never calls the real one.

**What I reviewed:** `git diff main...feature/optional-user`, with `main` (f082187) as the base and one commit, ec6fc35. It touches `users.py`, `profile.py`, `tests/test_users.py` and adds `PR.md`. I ran everything in temporary worktrees, which I've since removed. Your checkout wasn't touched and is still on `feature/optional-user`, clean.

## Should it exist?
The goal is to make "no such user" a return value instead of an exception, so callers don't need try/except. That's reasonable. A cheaper option would be to keep `get_user` as it is and add a `find_user()` that returns `None`, so existing callers keep working. The way the PR does it is fine too, as long as every caller is updated, and one wasn't.

## Blocker

**`billing.py:9-12`: checkout crashes for users that don't exist** (proven)
- **The claim:** "Pure refactor, no behaviour change for known users." That's true only for known users. Unknown users are the case that changed.
- **The path:**
  1. `price_for` calls `get_user(user_id)["tier"]`.
  2. `get_user` now returns `None`.
  3. `None["tier"]` raises `TypeError`, not `KeyError`.
  4. `except KeyError` doesn't catch it, so the error goes up to the checkout.
- **Before and after, same code run on both branches:**
  ```
  main:    price_for('nobody', 1000) -> 1000
  feature: price_for('nobody', 1000) -> RAISES TypeError 'NoneType' object is not subscriptable
  ```
- **Fix:** do the same thing the PR already did in `profile.py`:
  ```python
  user = get_user(user_id)
  if user is None:
      return amount_cents
  return round(amount_cents * (1 - DISCOUNT.get(user["tier"], 0)))
  ```

## Major

**`tests/test_billing.py:12`: the billing test can't catch this** (proven)
- It replaces `get_user` with a fake that raises `KeyError`, so it checks the old behaviour, not the real one. All 4 tests pass on both `main` and the feature branch, even though billing is broken on the feature branch.
- **Fix:** delete the fake from the unknown-user test, or make it return `None`. Better still, call the real `get_user` with an unknown id (the user table is a small in-memory dict) so the test notices if this changes again.

## Minor

**`profile.py:7`: `if user` would also treat an empty user record as missing** (traced)
- Today any found user is a non-empty dict, so this never happens. Using `if user is not None` states the intent and is safer.

## What I checked
- **Who calls `get_user`:** there are only two callers, `profile.py` (updated, and still returns "Guest" for unknown users: proven) and `billing.py` (not updated, broken). I also searched for other `KeyError` handlers and found only `billing.py:11`.
- **The key assumption:** "every caller treats a missing user the same after the change". The probe above shows it's false: the unchanged billing code fails on the feature branch and works on `main`.
- **Unknown:** code outside this repo that imports `users.get_user` and catches `KeyError` would break the same way. I can't see any from here.