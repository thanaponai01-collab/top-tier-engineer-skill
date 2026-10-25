I've removed `/v1/export`, but it did still have one caller. The nightly `finance-ledger-export` job in `jobs/nightly.yaml` called `/v1/export` and delivered the result to finance's SFTP ledger. The web app had moved to v2, but this job hadn't. If I'd only deleted the endpoint, that job would have started getting a 404 every night, and no test would have caught it.

**What changed**
- **`jobs/nightly.yaml`:** the finance job now calls `/v2/export?fmt=csv`, the replacement listed in `DEPRECATIONS.md`. I checked that it returns exactly the same CSV, header and rows, as v1 did.
- **`handlers/export_v1.py`:** deleted.
- **`app.py`:** removed the `/v1/export` route and the import for it. That path now returns 404.
- **`tests/test_export.py`:** removed `test_v1_csv`. The two v2 tests still pass.
- **`DEPRECATIONS.md`:** the entry is marked as removed on 2026-10-26, with a note that the finance job moved to v2.

**How it was checked**
I recorded the scheduler, the v1 and v2 export calls, and the test suite on the original code, then reran them all after the change:
- The scheduler and both v2 calls give the same output as before, and the finance job still returns 200.
- The only two differences are the intended ones: `/v1/export` now returns 404, and the test suite runs one fewer test.
- Every place that read what I changed was actually run during those checks.

**Not covered**
- **Callers outside this repo:** anything outside this repo that calls `/v1/export` directly, such as scripts, partners or old bookmarks, will now get a 404. I can't see those from here.
- **SFTP delivery:** the scheduler here only dispatches the job and records its status. I couldn't test the delivery to SFTP itself, but it gets the same response it got before.

Nothing broke along the way, and I deleted the `.evolve/` working folder afterwards. If the finance job should be handled differently, for example moved by its owners, the change to `nightly.yaml` is one line and easy to revert.