I removed the v1 export endpoint, but it did still have a caller. The nightly `finance-ledger-export` job (`jobs/nightly.yaml:3`) was calling `/v1/export` and sending the result to `sftp://finance.example.internal/ledger/`. Deleting the route by itself would have turned that job into a 404. I switched it to `/v2/export?fmt=csv`, which returns exactly the same CSV, so finance gets the same file.

**Changed:**
- **`handlers/export_v1.py`:** deleted.
- **`app.py`:** removed the `export_v1` import and the `/v1/export` route.
- **`tests/test_export.py`:** removed `test_v1_csv`; the two v2 tests remain.
- **`jobs/nightly.yaml`:** the finance job now calls `/v2/export?fmt=csv`.
- **`DEPRECATIONS.md`:** the entry now says when v1 was removed and that the job moved to v2.

**Before and after:** I recorded 6 commands on the original code and reran them after the change.
- Five print exactly what they printed before. These include `python scheduler.py` and a run that prints what each nightly job actually returns, so the finance job's CSV is confirmed unchanged.
- The test suite changed on purpose: 3 tests became 2, because `test_v1_csv` was testing the endpoint I removed. The remaining tests pass.
- All 4 places in the code that read what I changed were exercised by those runs.

**Broke along the way and fixed:** nothing broke after the edit. The finance job would have broken if I had removed the route without moving the job first.

**Not covered:** anything outside this repo that calls `/v1/export` will now get a 404. That includes other services, scripts, or anyone hitting the URL by hand, and there's no access log here to check. If you have server logs, it's worth checking them for recent v1 hits before you deploy. Also, the finance team may want to know their job's URL changed, even though the file they receive is the same.

I deleted the `.evolve/` working folder afterwards.