I haven't removed the v1 endpoint. Something does still use it: the nightly finance job.

**What I found**

- `jobs/nightly.yaml:2-4` sets up a job called `finance-ledger-export` with `url: /v1/export`, delivered to `sftp://finance.example.internal/ledger/`. `scheduler.py` sends it through the app router every night at 02:00.
- I ran `python scheduler.py` and that job returns `finance-ledger-export 200` today. If I removed the route as asked, it would get a 404 and the finance ledger would stop being delivered. The only sign would be a 404 in the scheduler output.
- You're right about the web app; there's no web app code here that calls v1. But the batch job was missed. `DEPRECATIONS.md` says to remove the endpoint once there are no callers left, and that isn't true yet.

**The fix is cheap.** `/v2/export?fmt=csv` returns exactly the same status and body as `/v1/export`; I compared the two outputs directly. So moving the finance job to v2 shouldn't change anything finance receives.

**Proposed steps (not yet done):**
1. Change `jobs/nightly.yaml` to `url: /v2/export?fmt=csv`, then rerun `scheduler.py` and check it still gets a 200.
2. Remove the `/v1/export` route and import from `app.py`, delete `handlers/export_v1.py` and the `test_v1_csv` test, mark the row in `DEPRECATIONS.md` as removed, then rerun the tests. All 3 currently pass.

**One thing I can't check from here:** whether anything outside this code calls `/v1/export`, such as other teams or scripts. If you have access logs for the last few weeks showing no v1 traffic, that would settle it. Otherwise, it's your call whether to accept that risk.

Should I go ahead with both steps? Or should I do step 1 only and leave v1 in place for a night or two, so the finance delivery is confirmed on v2 before the endpoint goes?