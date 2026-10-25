"""python -m depot.jobs: run every job in schedule.json (the host's cron calls this nightly)."""
import importlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "schedule.json"), encoding="utf-8") as fh:
    for name in json.load(fh)["nightly"]:
        importlib.import_module(f"depot.jobs.{name}").run()
