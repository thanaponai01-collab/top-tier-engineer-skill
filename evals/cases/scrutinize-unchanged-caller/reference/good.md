# Scrutinize: feature/optional-user vs main

Read with `git diff main...feature/optional-user` (users.py, profile.py, tests/test_users.py, PR.md).

**Verdict: fix-then-ship.** It is not a pure refactor. `billing.py` is outside the diff and breaks:
`price_for` still expects `get_user` to raise `KeyError`.

**Blocker: billing.py:9 `price_for`**: `get_user(user_id)["tier"]` inside `try/except KeyError`.
Now `get_user("nobody")` returns `None`, so it evaluates `None["tier"]`, which raises `TypeError: 'NoneType' object is
not subscriptable`. The except no longer catches it, and checkout crashes for every unknown or guest
user who used to pay list price. [proven: `python -c "import billing; billing.price_for('nobody', 1000)"`
→ TypeError on the branch; returns 1000 on main]

**Major: tests/test_billing.py mocks around it.** `mock.patch("billing.get_user", side_effect=KeyError)`
keeps testing the old contract, so the suite is green. Replace the mock with the real `get_user`.

Smallest fix: `user = get_user(user_id); if user is None: return amount_cents`, plus a billing test
that uses the real lookup for an unknown id. Cheaper alternative weighed: keep raising and add
`find_user()` returning None for new callers. That avoids touching existing callers at all.


The decisive safety assumption is that a missing user still reaches checkout at list price. I probed the unchanged `billing.price_for` boundary against both implementations: the branch raises TypeError, while main returns 1000. That distinguishes the unsafe contract change from the safe behavior we need to preserve.
