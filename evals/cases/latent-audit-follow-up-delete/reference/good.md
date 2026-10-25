I deleted only `app/jobs/vacuum_store.py`. The other two are not dead, so I left them:

- `app/jobs/rollup_daily.py` is loaded by name: `schedule.json` lists `rollup-daily`, and
  `run_all` imports `app.jobs.rollup_daily` from that name, so the nightly `run-jobs` needs it.
- `app/exporters/yaml_report.py` is loaded by name too: `load_exporter` imports
  `<fmt>_report` for `inv.py export yaml`.

Nothing imports either one directly, which is why they look dead. `.latent/` recorded both as
reached by name, and deleting them in a copy makes `run-jobs` and `export yaml` fail.
