**Verdict: rework.** This is not a pure refactor. It breaks checkout for any user ID that isn't found. `billing.py` still expects `get_user` to raise `KeyError`. Now it gets `None` back, indexes into it, and crashes with `TypeError`. The tests still pass because the billing test mocks `get_user` with the old behaviour.

**What I reviewed:** `git diff main...feature/optional-user` in `fixture/`. That's one commit, `ec6fc35`, on top of `f082187`, and it changes `users.py`, `profile.py`, `tests/test_users.py` and adds `PR.md`.

**A mistake on my part, now undone:** my first attempt to create a scratch worktree failed because your checkout already has this branch. My command didn't stop at that error. It ran `git checkout main` and some Python in your own checkout. I switched you back to `feature/optional-user` (still at `ec6fc35`, nothing changed) and deleted the `__pycache__/` folders that run created. All results below come from a separate detached worktree, which I've removed. `git worktree list` now shows only your checkout.

### Should it exist?
Goal: callers stop needing `try/except KeyError` around `get_user`. That's reasonable. The cheaper, safer option is to leave `get_user` alone and add a separate `find_user()` that returns `None`, then move callers over one by one. Changing the meaning of an existing function means every caller has to change in the same PR, and this PR missed one.

### Blocker
**`billing.py:9-12`: `price_for` crashes for unknown users.** This file isn't in the diff.
- Claim: "no behaviour change." Path: `price_for("nobody", 1000)` → `get_user` now returns `None` → `None["tier"]` raises `TypeError`, which `except KeyError` doesn't catch. Doesn't hold.
- Consequence: guests and anyone whose user record is missing can no longer get a price. Before, they paid list price (the docstring says "anyone we can't find pays list price"). Now checkout throws.
- Evidence: **proven** by running it in the scratch worktree:
  - main: `price_for('nobody',1000)` → `1000`, `price_for('u1',1000)` → `900`
  - feature: `price_for('nobody',1000)` → `TypeError: 'NoneType' object is not subscriptable`
- Smallest fix: in `billing.py`, do `user = get_user(user_id)`, `if user is None: return amount_cents`, matching what `profile.py` now does. Or don't change `get_user` and add a separate `find_user()` instead.

### Major
**`tests/test_billing.py:12`: the test that should have caught this mocks around it.** It uses `mock.patch("billing.get_user", side_effect=KeyError("nobody"))`, so it keeps simulating the old contract. That's why "tests are green" is true but means nothing here (**proven**: 4 tests, OK, on the branch). Fix: change the mock to `return_value=None`, or better, drop the mock and call `price_for("nobody", 1000)` against the real `get_user`. Either version fails on this branch and passes once billing is fixed.

### Minor
- **`profile.py:7`:** `if user` tests whether the value is truthy, not whether it's `None`. An empty-dict user would show as "Guest". That can't happen with today's data; `is not None` states the intent better.

### What I checked and what's fine
- `profile.display_name`: same output as main for unknown users (`Guest`) and known ones (`Ada`). **Proven.**
- The decisive assumption: every caller of `get_user` handles the new `None` return. I grepped for `get_user`/`KeyError`: the only callers are `profile.py` and `billing.py`, and billing fails. **Traced and proven.** Code outside this repo that imports `users.get_user` is **unknown**.

I haven't posted anything on the PR.