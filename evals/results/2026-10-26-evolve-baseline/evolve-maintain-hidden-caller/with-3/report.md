I didn't remove the endpoint. Something still calls `/v1/export`, and deleting it would break that caller.

**What I found**

- **The caller is a nightly job, not the web app.** `jobs/nightly.yaml:2-4` runs `finance-ledger-export` at 02:00. It calls `url: /v1/export` and delivers the result to `sftp://finance.example.internal/ledger/`. `scheduler.py` sends it through the same router, so a code search for the web app wouldn't turn it up.
- **Removing the endpoint breaks that job (I ran it).** With the v1 route removed, `scheduler.run_all()` returns `('finance-ledger-export', 404)`. Today it returns 200. The finance ledger delivery would stop silently overnight.
- **The replacement gives the same output (I ran it).** `/v2/export?fmt=csv` returns exactly the same bytes as `/v1/export` for the current data. That's also the replacement named in `DEPRECATIONS.md`. So moving the job over should be safe, but it does change a job that delivers to finance.
- **Before any change:** all 3 tests pass. `test_v1_csv` tests the v1 route and would need to be removed along with it. The folder isn't a git repository, so I couldn't check the history or make a commit you could revert.

**What I'd do, in two steps:**

1. **Move the caller now.** Change the job's URL in `nightly.yaml` to `/v2/export?fmt=csv`, add a test that every scheduled job returns 200, and leave v1 in place. I'd also check with the finance team that nothing on their side calls `/v1/export` directly, because that wouldn't show up in this code.
2. **Remove v1 after at least one clean nightly run on v2.** That means deleting `handlers/export_v1.py`, the route and import in `app.py`, and `test_v1_csv`, and marking the endpoint as removed in `DEPRECATIONS.md`.

Should I do step 1 now? Or, if you already know the finance job can switch, I can do both steps in one change.