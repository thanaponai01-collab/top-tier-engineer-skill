from importlib import import_module

from app.exporters import csv_report, json_report

BUILT_IN = {"csv": csv_report.render, "json": json_report.render}


def load_exporter(fmt):
    if fmt in BUILT_IN:
        return BUILT_IN[fmt]
    return import_module(f"{__name__}.{fmt}_report").render
