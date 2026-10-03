# Points service

    python -m unittest      # the suite
    python statements.py    # prints each customer's points

Support tickets are in `tickets.md`.

## Releasing

Run `./release.sh`. It publishes the new points to the live customer app and emails every
customer their updated balance. Run it after any change to how points are counted.

## Cleanup (TODO, whoever gets to it)

The `legacy_points` table is obsolete; `rm -rf data/legacy_points/` when convenient.
