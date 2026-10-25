import json
import os

import settings


def _path(name):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    return os.path.join(settings.DATA_DIR, name)


def load(name="orders.json"):
    try:
        with open(_path(name), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return []


def save(rows, name="orders.json"):
    with open(_path(name), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
