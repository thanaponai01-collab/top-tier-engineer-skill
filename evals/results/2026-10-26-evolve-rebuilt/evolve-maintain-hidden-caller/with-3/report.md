I removed the v1 export endpoint, but it did still have a user. The nightly **`finance-ledger-export`** job (`jobs/nightly.yaml:3`) was calling `/v1/export` and sending the result to finance's SFTP server. The web app had moved to v2, but this job hadn't. If I had only deleted the route, that job would have started getting a 404 every night, and none of the tests would have caught it.

So I switched that job to `/v2/export?fmt=csv`, which `DEPRECATIONS.md` already lists as the replacement. Before making any changes I checked that it returns exactly the same CSV as v1, byte for byte. The finance export should be unaffected, but you may want to let whoever owns that job know.

**Changes:**
- `app.py`: removed the `/v1/export` route and its import. It now returns 404.
- `handlers/export_v1.py`: deleted.
- `jobs/nightly.yaml`: the finance job now uses `/v2/export?fmt=csv`.
- `tests/test_export.py`: replaced `test_v1_csv` with a test that v1 returns 404, plus a new test that every nightly job's URL gets a 200. That would have caught this.
- `scheduler.py`: `load_jobs` now closes the job file properly. The new test exposed that it was leaving it open, which caused a warning.
- `DEPRECATIONS.md`: the entry now says v1 was removed and the job was moved.

**Check:** I recorded 8 commands on the original code (the scheduler, the nightly job outputs, `app.py` on each export URL, and the test suite) and reran them on the changed code. Six give identical output, including the finance job's CSV. Two changed on purpose: `/v1/export` now returns 404, and the suite now has 4 tests instead of 3, all passing. The helper's final check passed: all 5 places that use the changed code were run by those commands. I deleted `.evolve/` afterwards.

- **Broke along the way and fixed:** the new nightly-jobs test brought up the open-file warning in `scheduler.py`, now fixed. Two of my early recordings got a false 404 because the shell turned `/v1/export` into a Windows path. I re-recorded them correctly, and the comparison used the corrected runs.
- **Not covered:** anything outside this repo that calls `/v1/export` directly over HTTP, such as other services, scripts or bookmarks. Only the server's access logs would show those. There's no stored data involved, since v1 only read the in-memory order list.