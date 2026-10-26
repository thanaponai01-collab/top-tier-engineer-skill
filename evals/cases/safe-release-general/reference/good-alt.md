Safe to ship, staged: tonight only adds the cents column (expand); dropping the float `total` waits
for a later deploy once the worker runs the new code.

The worker still reads `total` and will keep running the old code during the 40-minute restart window,
so I kept `total` and made the new code write both. Tried on a copy of the database: up converts every
amount exactly (rounding, not truncating), the old invoice worker's numbers don't change, and the down
migration (`migrate.py down 2`) brings the old schema back. Note the documented rollback only runs
migrations up; to back out, run the down migration before restarting the old version.
