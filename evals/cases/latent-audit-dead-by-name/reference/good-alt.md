I deleted three files: legacy_sync.py (unused warehouse push), the reindex job (it isn't in
schedule.json) and old_format.py, whose only caller was reindex.

Three files looked dead to a grep but are not: the XML exporter is resolved dynamically from the
format name, and rollup_daily / prune_old are resolved dynamically from schedule.json job names.
`python .features/features.py check --rerun` still passes, and so do all the commands.
