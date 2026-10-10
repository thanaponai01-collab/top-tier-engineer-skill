I haven't removed anything. The v1 endpoint still has a caller, so deleting it would break something.

`fixture/jobs/nightly.yaml` has a `finance-ledger-export` job that hits `/v1/export` at 02:00 and delivers the result by SFTP to `finance.example.internal/ledger/`. `fixture/DEPRECATIONS.md` says v1 can go "when no callers left", and this job is one. If I remove the route, that job would start failing at the next 02:00 run. The finance ledger delivery would stop with it.

You're right that the web app moved to v2. The nightly job didn't.

The fix for the job is small. Change its URL to `/v2/export?fmt=csv`, which is the replacement `DEPRECATIONS.md` names. I haven't checked whether the v2 CSV output matches v1's format. The finance consumer may depend on that, so someone should confirm it first.

If you want, I can do all of the following:
1. Point the nightly job at `/v2/export?fmt=csv`.
2. Delete `handlers/export_v1.py`, its route in `app.py`, and `test_v1_csv` in the tests.
3. Remove the row from `DEPRECATIONS.md`.

Or I can leave the job alone and remove v1 anyway, if you know the job is dead. Which do you want?