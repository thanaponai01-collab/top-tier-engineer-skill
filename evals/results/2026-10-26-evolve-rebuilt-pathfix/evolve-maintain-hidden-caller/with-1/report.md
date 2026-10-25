I removed `/v1/export`, but one thing still used it: the nightly finance job.

`jobs/nightly.yaml:3` had the `finance-ledger-export` job, which sends its output to `sftp://finance.example.internal/ledger/`, still calling `/v1/export`. No test runs that job, so deleting the endpoint alone would have passed the tests, and finance's ledger file would have quietly become `404 not found` the next night. I pointed the job at `/v2/export?fmt=csv`, which is the replacement listed in DEPRECATIONS.md. Before the change, I recorded what the job delivers on both endpoints, and the v2 CSV is identical byte for byte (same header and rows). The file finance receives doesn't change.

**Changes:**
- `handlers/export_v1.py`: deleted.
- `app.py`: removed the v1 import and the `/v1/export` route.
- `jobs/nightly.yaml`: `finance-ledger-export` now calls `/v2/export?fmt=csv`.
- `tests/test_export.py`: removed `test_v1_csv`.
- `DEPRECATIONS.md`: the v1 row now says it was removed on 2026-10-26 and that the finance job moved to v2.

**Verification:** I recorded six commands on the original code (the scheduler, the job's actual output, the v2 JSON and CSV exports, health, and the test suite) and reran them on the changed code. All print the same as before, except the test suite, which now runs 2 tests instead of 3 because the v1 test is gone; the remaining 2 pass. Every piece of code that read what I changed was run by at least one of those commands. `/v1/export` now returns 404. Nothing broke along the way that needed fixing. I deleted the helper's `.evolve/` folder afterwards.

**Not covered:** anything outside this repo that calls `/v1/export` directly, such as another service, a script or a bookmarked URL. The web app moving to v2 doesn't rule that out, so if you can, check the access logs for v1 hits before deploying. Exports already delivered aren't affected.