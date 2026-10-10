Don't merge this as-is. It changes a contract that a file it didn't touch depends on.

The branch makes get_user return None instead of raising KeyError, and fixes profile.py for that.
But billing.py's price_for does `get_user(user_id)["tier"]` and relies on `except KeyError` to send
unknown users to list price. After this change an unknown user gives `None["tier"]`, a TypeError that
nothing catches, so checkout fails for guests. I ran it on the branch and got a TypeError; on main
it returns 1000.

Why CI didn't notice: test_billing patches get_user with a KeyError side effect, so it tests the
behaviour the branch just removed.

Verdict: rework the billing caller (and its test to use the real function) before merging. Or keep
the raising version and add a separate optional lookup.
