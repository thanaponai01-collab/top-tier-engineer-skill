**Verdict: rework (don't merge as is).** The PR isn't a pure refactor. It breaks checkout pricing for unknown users, and the green tests don't catch it.

I read `git diff main...feature/optional-user` (main as base, 4 files) and ran the tests on the branch.

**Goal:** make `get_user` return `None` instead of raising `KeyError` for unknown users. The cheaper alternative is to leave `get_user` alone and add a separate `find_user` that returns `None`. That changes no existing caller and gives the profile page the same simplification.

**Blocker: `billing.py:10` crashes for unknown users (proven)**
- `price_for` still relies on `get_user` raising `KeyError`: `try: tier = get_user(user_id)["tier"] except KeyError: return amount_cents`. The PR didn't touch `billing.py`.
- On the branch, `billing.price_for('nobody', 1000)` raises `TypeError: 'NoneType' object is not subscriptable`. On main it returns 1000. The `except KeyError` no longer matches, so guests and unknown IDs get an exception at checkout instead of list price.
- The PR text says "updates the profile page to match", but there are two callers (`profile.py` and `billing.py`) and only one was updated.
- **Fix:** either update `billing.py` to handle `None`, or use the `find_user` alternative above.

**Major: the tests hide the break (traced)**
- `tests/test_billing.py:12` mocks `billing.get_user` with `side_effect=KeyError("nobody")`. That simulates the old behavior, so it passes whatever the real `get_user` does.
- The branch's 4 tests pass (I ran them), but none exercises the real `get_user` through `price_for`.
- **Fix:** add a billing test that uses the real `get_user` with an unknown ID. Alternatively, change the mock to `return_value=None`, which fails until `billing.py` is fixed.

**Minor: contract change (traced)**
- Any caller outside this repo that catches `KeyError` from `get_user` breaks silently. I only checked callers inside this repo.
- The docstring is updated, but the change is a public behavior change, not a refactor. The PR title and description should say so.

**What I traced and ran:**
- All `get_user` call sites: `profile.py` (correct on the branch), `billing.py` (broken), and the tests.
- The branch test suite (4 tests, OK).
- The `price_for` failure above.

I posted nothing on the PR and left the checkout on main.