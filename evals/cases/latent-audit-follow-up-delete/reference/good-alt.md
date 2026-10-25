Removed vacuum_store.py: it isn't in the job schedule, so it never runs.

Did not remove the other two. Your teammate is right that no import names them, but they are
resolved dynamically: rollup_daily is a scheduled job (run-jobs loads it from its schedule entry,
rollup-daily), and yaml_report is what `export yaml` loads from the format name. Deleting either
breaks a command the nightly cron or a user runs.
