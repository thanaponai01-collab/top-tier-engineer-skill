"""Run by the host's cron: `python -m jobs.runner`. Runs every job in schedule.json."""
import importlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "schedule.json"), encoding="utf-8") as fh:
        for entry in json.load(fh):
            importlib.import_module(f"jobs.{entry['job']}").run()


if __name__ == "__main__":
    main()
