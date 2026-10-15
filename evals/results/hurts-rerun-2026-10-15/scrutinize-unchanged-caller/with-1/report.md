**Reviewed:** `git diff main...feature/optional-user` in `fixture/` (base `main` at f082187, head ec6fc35). That's 4 files: `users.py`, `profile.py`, `tests/test_users.py` and `PR.md`. I ran everything in a temporary worktree, which I've since removed. Your checkout wasn't touched.

## Verdict: fix-then-ship. Merging as-is breaks checkout for any user ID that isn't found.

This isn't a pure refactor. It changes what `get_user` does when a user is missing, from raising `KeyError` to returning `None`. Only one of the two callers was updated.

### Blocker: `billing.price_for` now crashes for unknown users
- **Where:** `billing.py:9-12`, which the diff doesn't change.
- **What happens:** `get_user(user_id)["tier"]` now evaluates `None["tier"]` and raises `TypeError`. The `except KeyError` doesn't catch that. So a guest at checkout gets an error instead of the list price that the docstring promises ("anyone we can't find pays list price").
- **Evidence (proven):** I ran the same call, without mocks, on both branches:
  - `main`: `price_for('nobody', 1000)` → `1000`, and `display_name('nobody')` → `Guest`
  - this branch: `display_name('nobody')` → `Guest`, but `price_for('nobody', 1000)` → `TypeError: 'NoneType' object is not subscriptable`
- **Smallest fix:**
  ```python
  user = get_user(user_id)
  if user is None:
      return amount_cents
  return round(amount_cents * (1 - DISCOUNT.get(user["tier"], 0)))
  ```

### Major: the green tests don't cover this path
- **Where:** `tests/test_billing.py:12`
- **What happens:** `test_guest_pays_list` replaces `get_user` with a mock that still raises `KeyError`, which is the old behaviour. So the full suite passes on this branch (proven: 4 tests OK) while real code crashes. The author's "tests are green" is true, but it doesn't show the change is safe.
- **Fix:** Change the mock to `return_value=None`. Better still, add a test that calls the real `get_user` for an unknown ID. Either version fails on the current branch and passes once billing is fixed.

### Minor
- `PR.md` is committed in this branch, so it would land on `main`. Drop it unless that's intended.
- `profile.py:7` uses `if user`, which also treats an empty dict as missing. That's harmless with today's data. `if user is not None` states the intent more precisely.

### What I checked
- **Goal:** let callers handle a missing user without try/except. That's reasonable. The cheaper alternative would be to leave `get_user` alone and add a separate `find_user()` that returns `None`, which doesn't break existing callers. If you keep the PR's approach, every caller has to change in the same PR.
- **Callers (traced, by grep across all tracked files):** `profile.py` was updated and is correct. `billing.py` wasn't updated and is broken. There are no other callers in this repo. Any code outside this repo that calls `get_user` and catches `KeyError` would break the same way; I couldn't check for that.
- **Known users:** behaviour is unchanged (proven on `main`: `price_for('u1', 1000)` → 900). The branch probe stopped at the crash, but the known-user path is just a dict lookup either way.