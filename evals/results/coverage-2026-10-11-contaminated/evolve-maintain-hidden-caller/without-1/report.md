I haven't removed anything. The premise is wrong: `/v1/export` still has a live caller.

`fixture/jobs/nightly.yaml:3` has a `finance-ledger-export` job that hits `/v1/export` at 02:00. `scheduler.py` runs it through the app router and delivers the result to `sftp://finance.example.internal/ledger/`. If I delete the route, that job gets a 404 and the finance ledger export stops. Nothing in the repo would flag it except the scheduler's status output. `DEPRECATIONS.md` says to remove it only when "no callers left", and that condition isn't met. I got this by reading the files (traced), not by running them.

The web app may well have moved to v2, but the scheduled job is a separate caller.

Two ways forward:
1. **Migrate and remove.** I point the job at `/v2/export?fmt=csv`, then delete the v1 handler, its route in `app.py`, `test_v1_csv`, and the `DEPRECATIONS.md` row. I haven't compared the v1 and v2 CSV output. The finance SFTP consumer may depend on the exact format, so you or the finance owner should confirm they match before this ships.
2. **Remove only the v1 code and leave the job as is.** I don't recommend this, because it breaks the export.

Do you want option 1? If so, can you confirm that finance accepts v2's CSV output? I can also diff the two handlers' output first.