"""Cron entry point. Resolves job names from settings at runtime."""
import importlib

from settings import SCHEDULED_JOBS


def run_all():
    for spec in SCHEDULED_JOBS:
        module_name, func_name = spec.split(":")
        module = importlib.import_module(module_name)
        getattr(module, func_name)()


if __name__ == "__main__":
    run_all()
