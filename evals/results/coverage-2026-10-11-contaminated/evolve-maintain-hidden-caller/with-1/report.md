I removed the v1 export endpoint, but "nothing uses it" was wrong. `jobs/nightly.yaml` still called `/v1/export` in the `finance-ledger-export` job, which runs nightly and delivers to `sftp://finance.example.internal/ledger/`. I moved that job to v2 first. I ran the tests and the scheduler locally. I did not deploy anything.

- **Job moved:** the job's URL is now `/v2/export?fmt=csv`. In a local run, v1 and v2 `fmt=csv` returned identical status and body, so the file finance receives should be unchanged (proven).
- **Endpoint removed:** I deleted `handlers/export_v1.py` and took the route and import out of `app.py`.
- **Tests:** the old `test_v1_csv` is now `test_v1_removed`, which expects a 404. I added `test_nightly_jobs_resolve`, which fails if any nightly job URL stops returning 200, so a missed caller shows up in CI. All 4 tests pass.
- **Docs:** `DEPRECATIONS.md` now records the removal on 2026-10-11.

Before you deploy, check that no other consumer calls `/v1/export` directly, such as outside scripts, other services or the finance side. I could only search this repo. To roll back, restore `export_v1.py` and the route and point the job back at `/v1/export`.