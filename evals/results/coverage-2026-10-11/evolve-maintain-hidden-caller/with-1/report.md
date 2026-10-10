I removed the v1 export endpoint, but "nothing uses it" wasn't true: the nightly finance job was still calling it. I moved that job to v2 first, then deleted v1. All 4 tests pass, and `python scheduler.py` returns 200 for both nightly jobs.

**The caller I found:** `jobs/nightly.yaml` had `finance-ledger-export` hitting `/v1/export` at 02:00 and delivering the result to `sftp://finance.example.internal/ledger/`. Deleting v1 alone would have made that job get a 404 on its next run.

**What I changed in `fixture/`:**
- **Job:** `jobs/nightly.yaml` now calls `/v2/export?fmt=csv`. Before the switch I checked that the v1 and v2-CSV responses are byte-identical, so the file delivered to finance doesn't change.
- **Endpoint:** I deleted `handlers/export_v1.py` and its route and import in `app.py`.
- **Tests:** `test_v1_csv` is now `test_v1_removed`, which expects a 404. A new `test_nightly_jobs_resolve` fails if any scheduled job points at a missing route, which is what would have caught this.
- **Docs:** `DEPRECATIONS.md` marks v1 as removed.

**Still to do:**
- **Deploy:** I only changed the repo. Deploy the `nightly.yaml` change together with the removal, or the live job will break.
- **Callers outside this repo:** I can only see this repo. Any other consumer of `/v1/export`, such as a different scheduler or finance's own tooling, would now get a 404. Check access logs if you can.
- **Leftover files:** a stale `__pycache__/export_v1*.pyc` remains. It's harmless and can be deleted.