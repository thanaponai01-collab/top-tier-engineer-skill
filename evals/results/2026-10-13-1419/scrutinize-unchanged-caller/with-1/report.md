**Verdict: rework. Don't merge this yet.** It isn't a pure refactor. `billing.py` didn't change and still expects `KeyError`, so on this branch checking out with an unknown user now crashes with `TypeError` instead of charging list price. The tests pass only because the billing test fakes the old `KeyError`.

**What I reviewed:** `git diff main...feature/optional-user` (one commit, `ec6fc35`), plus the files the diff doesn't touch: `billing.py` and `tests/test_billing.py`.

**Goal:** Make `get_user` return `None` for unknown users so callers don't need try/except. That's a reasonable goal, but it changes the function's contract, and every caller has to change with it. Only one of the two callers did.

### Blocker
**Checkout crashes for unknown users.** `billing.py:9-12` (not in the diff)
- **What breaks:** `price_for` does `get_user(user_id)["tier"]` inside `except KeyError`. `get_user` now returns `None`, so `None["tier"]` raises `TypeError`, which that `except` doesn't catch. Anyone billing can't find now gets an error instead of list price, which is what the docstring promises.
- **Evidence (proven):** I ran `price_for("nobody", 1000)` in scratch worktrees:
  - `main`: returns `1000`
  - this branch: `TypeError: 'NoneType' object is not subscriptable`
- **Fix:** In `billing.py`, do the same as `profile.py`: `user = get_user(user_id)`, return `amount_cents` if `user` is `None`, otherwise read `user["tier"]`.

### Major
**The tests hide the bug.** `tests/test_billing.py:12`
- **What's wrong:** It patches `get_user` with `side_effect=KeyError(...)`, which tests the old contract. That's why "tests are green" on both branches.
- **Evidence (proven):** The suite printed `OK` on `main` and on this branch, while the real billing call failed.
- **Fix:** Change the mock to `return_value=None`, or better, drop it and call the real `get_user` with an unknown ID so this test follows any future change to the contract.

### Confirmed fine
- **Known users behave the same (proven):** `price_for("u1", 1000)` gives `900` and `display_name("u1")` gives `"Ada"`.
- **`profile.py` is correct (proven):** `display_name("nobody")` gives `"Guest"`.
- **Nothing else calls `get_user` (traced):** a grep finds only `profile.py` and `billing.py`. Code outside this repo is unknown.

### Minor
- `PR.md` is committed on the branch, so it would end up in `main` when merged. You probably don't want that.

### Housekeeping
- I used detached scratch worktrees, which are now removed.
- Your `fixture/` checkout wasn't switched. One early command ran in it by mistake and created `__pycache__/`; I deleted it. `git status` is clean.
- I posted nothing anywhere.