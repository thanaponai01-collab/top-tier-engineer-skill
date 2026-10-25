# FEATURES

What the system has and how each feature is reached. The commands that keep it true need
no skill installed; their `--help` says the rest, so the script never needs reading:
- `python .features/features.py check --rerun`: every entry point against the code, and every
  recorded run (.features/<feature>.json) run again, naming what moved or stopped working.
- `python .features/features.py prove --feature "<name>" [--copy] -- <command>`: run an entry
  point and record it (`--copy` runs it in a throwaway copy, for anything that writes data).
- status: `proven` (a passing run is recorded), `failing` (a failing run is recorded), `traced`
  (read start to end, not run) or `suspected`, then how you know.

## Add
- what: Add an item with a quantity to the stock file.
- cli: `add` @ inv.py
- trace: `main` @ inv.py > `add` @ app/store.py
- effect: a new row in items.json
- status: proven: ran `inv.py add` in a copy, new id printed

## List
- what: Print every item with its quantity.
- cli: `list` @ inv.py
- trace: `main` @ inv.py > `load` @ app/store.py
- status: proven: ran `inv.py list`

## Export
- what: Write the stock as CSV, JSON or XML to stdout.
- cli: `export` @ inv.py
- trace: `main` @ inv.py > `load_exporter` @ app/exporters/__init__.py > `render` @ app/exporters/xml_report.py
- status: proven: ran `inv.py export xml` and `inv.py export csv`

## Stats
- what: One-line stock summary, naming what is out of stock.
- cli: `stats` @ inv.py
- trace: `main` @ inv.py > `summary` @ app/report.py > `plural` @ app/util/text.py
- status: proven: ran `inv.py stats`

## Run Jobs
- what: Run the scheduled jobs once (daily rollup, pruning report), as the nightly cron does.
- cli: `run-jobs` @ inv.py
- trace: `main` @ inv.py > `run_all` @ app/jobs/__init__.py > `run` @ app/jobs/prune_old.py
- needs: app/jobs/schedule.json lists the jobs by name
- status: proven: ran `inv.py run-jobs`, both jobs reported
