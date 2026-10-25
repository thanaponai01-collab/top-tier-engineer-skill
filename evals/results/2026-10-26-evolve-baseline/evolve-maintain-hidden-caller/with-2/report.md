I haven't removed anything. `/v1/export` still has a live caller, so taking it out now would break a production job.

**The caller:** `fixture/jobs/nightly.yaml:2-4`. The `finance-ledger-export` job calls `/v1/export` every night at 02:00 and delivers the result to `sftp://finance.example.internal/ledger/`. The web app may well be on v2, but this scheduled job never moved.

**What I checked:**
- I ran `python scheduler.py`. It printed `finance-ledger-export 200`, so the job really does call v1. If v1 were removed, the router would return 404 and finance's ledger file would stop arriving. Nothing in this repo would alert anyone.
- The only other places v1 appears are the route in `app.py`, `handlers/export_v1.py`, `test_v1_csv`, and the row in `DEPRECATIONS.md`, whose removal condition ("no callers left") isn't met yet.
- **There is a safe path:** `/v2/export?fmt=csv` returns exactly the same bytes as `/v1/export` (I compared them, `identical: True`). The `DEPRECATIONS.md` row already names it as the replacement.
- All 3 existing tests pass.

**How I'd do it, in two steps:**
1. **Move the caller:** change the job's URL to `/v2/export?fmt=csv`, and add a test that fails if any job in `nightly.yaml` points at a route that doesn't exist. Then let it run for at least one night and confirm finance gets a correct file.
2. **Remove v1:** delete the route, `export_v1.py` and `test_v1_csv`, and update `DEPRECATIONS.md`.

**What I need from you:**
- **Can I change the finance job's URL?** It feeds an external finance system, so I didn't want to change it without your OK, even though the output is identical. Finance may also want to know about the change.
- **Are there callers outside this repo?** Other services, scripts or partners could hit `/v1/export` directly, and I can't see them from here. Access logs for that path would settle it.

If you approve step 1 and you're confident nothing outside the repo calls v1, I can do both steps now. That means v1 is removed before the switched job has run for a night, so there's no fallback if something goes wrong.