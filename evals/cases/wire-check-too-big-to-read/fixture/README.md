# depot

Warehouse operations CLI: stock in bins, inbound and outbound, orders, staff.

    depot help                 # every command
    depot <command> [args]
    depot-admin <command>      # operator tools
    python -m depot.jobs       # the nightly jobs (run by the host's cron)

Data lives in `$DEPOT_DATA` (default `./data`), seeded on first use.
