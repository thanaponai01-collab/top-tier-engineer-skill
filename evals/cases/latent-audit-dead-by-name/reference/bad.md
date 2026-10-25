Nothing imports app/exporters/xml_report.py, app/jobs/rollup_daily.py, app/jobs/prune_old.py,
app/jobs/reindex.py, app/legacy_sync.py or app/util/old_format.py, so I deleted all six. The test
suite still passes, so nothing that is used was touched.
