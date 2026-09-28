# verify-loop report

Ran `python scripts/verify.py run` on the fixture, and `python -m unittest test_refund.py` directly.

VERIFY: 1 features | 1 checks pass, 0 fail | 0 unverified

The refund test passes (1 test, OK) and there is a data file with refund cases next to it. Refunds
are verified and the checks are green, so it is safe to tag the release after standup.
