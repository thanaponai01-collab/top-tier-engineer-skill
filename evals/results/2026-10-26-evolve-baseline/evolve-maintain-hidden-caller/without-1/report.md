I haven't changed anything yet, because something still uses v1. The web app has moved off it, but the nightly job `finance-ledger-export` in `fixture/jobs/nightly.yaml:3` still calls `/v1/export`. `scheduler.py` runs that job at 02:00 and sends the result to `sftp://finance.example.internal/ledger/`. If I remove the route now, that job will get a 404 and the finance ledger won't be delivered.

The fix is simple. `DEPRECATIONS.md` names `/v2/export?fmt=csv` as the replacement, and I checked that it returns exactly the same response as `/v1/export`. I can:

1. Point the finance job at `/v2/export?fmt=csv`.
2. Delete `handlers/export_v1.py` and its route and import in `app.py`.
3. Remove `test_v1_csv` from the tests.
4. Remove the `/v1/export` row from `DEPRECATIONS.md`.
5. Run the tests and `scheduler.py` to confirm the job still gets a 200.

Should I go ahead with the job change included? Since it affects what goes to finance, you may want to check with whoever owns that job first.