Done, but "nothing uses it" wasn't quite true. The nightly finance export in jobs/nightly.yaml still
pointed at /v1/export. scheduler.py feeds those URLs through the router, so deleting the route would
have turned finance's 02:00 ledger file into a 404.

What I did:
- switched that job to /v2/export?fmt=csv. v2's CSV output is identical, which I checked by running
  both before the change;
- then removed the v1 route, its handler and its test, and marked it removed in DEPRECATIONS.md;
- ran the test suite and `python scheduler.py`: both jobs return 200.

Worth confirming with whoever owns finance's SFTP import, and checking HTTP logs for outside callers,
since the repo can't show those.
