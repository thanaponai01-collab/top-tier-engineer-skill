I haven't removed anything yet, because something still calls v1. The web app has moved to v2, but a nightly job hasn't.

`fixture/jobs/nightly.yaml:2-4`:
```yaml
- name: finance-ledger-export
  url: /v1/export
  deliver_to: sftp://finance.example.internal/ledger/
```
`scheduler.py` runs this job at 02:00 through the same router. If I delete the route, the finance ledger export will get a 404 every night. `DEPRECATIONS.md` also says to remove v1 only when "no callers left", and that isn't true yet.

There's an easy way through. `/v2/export?fmt=csv` returns exactly the same status and body as `/v1/export`; I checked by calling both through `app.dispatch`. So the removal could be:

1. Change the job's `url` to `/v2/export?fmt=csv`.
2. Delete `handlers/export_v1.py`, its import and its route in `app.py`, and `test_v1_csv`.
3. Remove the v1 row from `DEPRECATIONS.md`.

The first step changes a job that delivers files to finance, so I'd like your go-ahead before I do it. Whoever owns that job may want to know too. Should I go ahead with all three?