"""A JSON file as the database."""
import json
import os

from invoicing import models

PATH = os.environ.get("INVOICING_DB", "db.json")


def _read():
    if not os.path.exists(PATH):
        return {"orders": {}, "customers": {}}
    with open(PATH, encoding="utf-8") as fh:
        return json.load(fh)


def get(table, key):
    return dict(_read()[table].get(str(key)) or models.blank_order())


def put(table, key, value):
    data = _read()
    data[table][str(key)] = value
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
