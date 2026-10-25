Cause: `app.py` adds 11 cents where SPEC.md says the fee is 10. Fixed there. The new entry-point
check (`python checkout.py` must print 110) failed on the original code, printing 111, before the fix,
and passes now with the unit test. The live payment gateway remains outside coverage.
