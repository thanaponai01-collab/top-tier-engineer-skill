I removed `/v1/export`, but one thing was still using it: the nightly `finance-ledger-export` job in `jobs/nightly.yaml` called `/v1/export` and sends the result to the finance SFTP drop. The web app had moved to v2, but this job hadn't. Deleting the endpoint alone would have broken that job.

I moved it to `/v2/export?fmt=csv`, which `DEPRECATIONS.md` lists as the replacement. I compared the CSV the job gets before and after the change, and it is identical.

**What changed:**
- **`jobs/nightly.yaml`:** `finance-ledger-export` now calls `/v2/export?fmt=csv`.
- **`app.py`:** removed the `/v1/export` route and the `export_v1` import.
- **`handlers/export_v1.py`:** deleted.
- **`tests/test_export.py`:** replaced `test_v1_csv` with `test_v1_removed`, which checks that `/v1/export` now returns 404.
- **`DEPRECATIONS.md`:** the `/v1/export` row now says it was removed on 2026-10-26 and that the nightly job moved to v2.

**How I checked:** I recorded these commands on the original code and reran them on the changed code:
- `python scheduler.py`
- a script that prints the body each nightly job gets
- `app.py` called with `/v1/export`, `/v2/export`, `/v2/export?fmt=csv` and `/health`
- the test suite

Everything gives the same output as before except `/v1/export`, which now returns 404 as intended. The helper's gate passed: every piece of code that reads what changed was exercised by at least one of those commands. Afterwards I ran `scheduler.py` and the tests directly: both jobs returned 200 and the tests passed. Three of the recorded commands were mangled by the shell and only ever produced 404, so they proved nothing; I recorded them again correctly.

**Not covered:**
- **Callers outside this repo:** I couldn't see whether anything outside this repo still calls `/v1/export`. Check access logs before deploying.
- **The SFTP delivery:** `scheduler.py` doesn't implement delivery, so no run touched the SFTP side. The finance team should confirm the next ledger file arrives as usual.
- **Generated files:** I didn't check for stored data or generated files that mention v1.

I deleted the helper's `.evolve/` working folder afterwards.