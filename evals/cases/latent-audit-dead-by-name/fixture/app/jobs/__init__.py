import json, os
from importlib import import_module

SCHEDULE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.json")


def run_all(items):
    with open(SCHEDULE, encoding="utf-8") as fh:
        names = json.load(fh)["jobs"]
    for name in names:
        job = import_module(f"{__name__}.{name.replace('-', '_')}")
        yield f"{name}: {job.run(items)}"
