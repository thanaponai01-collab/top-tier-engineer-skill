I removed `/v1/export`, but one thing was still calling it. The nightly `finance-ledger-export` job (`jobs/nightly.yaml`, which delivers to the finance SFTP ledger) called `/v1/export`. It isn't the web app, so it was easy to miss. Removing the route alone would have made that job start getting 404s with no warning, and no test runs it.

**What I changed**
- **`jobs/nightly.yaml`:** the finance job now calls `/v2/export?fmt=csv`, the replacement listed in DEPRECATIONS.md. I compared the two outputs and the CSV is byte-for-byte the same (`id,customer,total` / `o1,acme,120.00` / `o2,globex,75.50`).
- **`app.py`:** removed the `/v1/export` route and the `export_v1` import.
- **`handlers/export_v1.py`:** deleted.
- **`tests/test_export.py`:** removed `test_v1_csv`. The two v2 tests still pass.
- **`DEPRECATIONS.md`:** marked `/v1/export` as removed on 2026-10-26, with a note that the finance job moved to v2.

**Checks**
I recorded six commands before the edit and reran them after: the scheduler, each endpoint, and the test suite.
- Four gave the same output as before, including `python scheduler.py`, where both jobs still return 200.
- Two changed on purpose: `/v1/export` now returns 404, and the test suite runs 2 tests instead of 3.
- All four places that read the changed code or name were exercised by at least one of those runs, including the job's line in `nightly.yaml`.
- Nothing broke along the way.

**Not covered**
- Anything outside this repo that calls `/v1/export` directly, such as other scripts, cron jobs or partner integrations. Request logs would show whether anything still does.
- `scheduler.py` only dispatches each job and prints its status; the SFTP delivery isn't in this repo, so I couldn't run it. Since the CSV is identical, finance's ledger import should see no difference, but it's worth watching after the next 02:00 run.

The `.evolve/` working folder has been deleted.