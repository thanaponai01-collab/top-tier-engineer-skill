# Remove /v1/export

**Class: Evolve (deprecation), long reach.** v1 had one caller left, and it isn't in the web app.

Callers counted before touching anything [traced: `grep -rn "v1/export"`]:
- `app.py` route table (the thing being removed)
- `tests/test_export.py::test_v1_csv`
- **`jobs/nightly.yaml` → `finance-ledger-export`**, which `scheduler.py` runs every night at 02:00 and
  delivers to finance's SFTP. It's a URL in a config file, so an import search never finds it.

Down the ladder:
1. Moved the caller: `finance-ledger-export` now calls `/v2/export?fmt=csv`. Same header, same rows
   [proven: `python scheduler.py` → `finance-ledger-export 200`, output byte-identical to v1's].
2. Removed the `/v1/export` route, `handlers/export_v1.py` and `test_v1_csv`. Updated DEPRECATIONS.md.
3. `python -m unittest discover -s tests` green before and after. `python scheduler.py` → all jobs 200.

Not checked: callers outside this repo (other services hitting `/v1/export` over HTTP). Access logs
for the last 30 days would prove it. Until then, a 410 with a pointer to v2 is safer than a silent 404.
