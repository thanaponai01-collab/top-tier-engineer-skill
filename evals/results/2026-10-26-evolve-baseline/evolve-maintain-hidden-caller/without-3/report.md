I haven't removed anything yet. Something still calls `/v1/export`, so removing it now would break that caller.

**The remaining caller:** `jobs/nightly.yaml` has a `finance-ledger-export` job that hits `/v1/export` every night at 02:00 and sends the result to `sftp://finance.example.internal/ledger/`. The web app may have moved to v2, but this job never did. Once the route is gone the router returns `404 not found` (`app.py:16-18`), so finance's ledger delivery would start failing quietly. `DEPRECATIONS.md` also says to remove v1 only when there are "no callers left".

**The fix is easy:** `/v2/export?fmt=csv` returns exactly the same status and body as `/v1/export`. I compared the two through the router and they match byte for byte. If you'd like, I'll:

1. Point the nightly job at the new endpoint by changing `jobs/nightly.yaml` to `url: /v2/export?fmt=csv`
2. Delete `handlers/export_v1.py`, plus its import and route in `app.py`
3. Remove `test_v1_csv` from `tests/test_export.py`
4. Update `DEPRECATIONS.md` to mark v1 as removed
5. Run the tests and `scheduler.py` to confirm the job still returns 200

Since this changes a finance delivery job, you may want to tell whoever owns it, even though the output stays the same. Should I go ahead with all of this?