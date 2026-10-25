"""JSON store, one file per collection, seeded on first use."""
import json
import os

from depot import settings


def _path(name):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    return os.path.join(settings.DATA_DIR, f"{name}.json")


def seed(name):
    return [{"id": i, "name": f"{name}-{i}", "qty": (i * 7) % 23 + 3, "age": (i * 5) % 40,
             "zone": "ABCD"[i % 4], "tag": f"t{i % 6}"} for i in range(1, 13)]


def load(name):
    try:
        with open(_path(name), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return seed(name)


def save(name, rows):
    with open(_path(name), "w", encoding="utf-8") as fh:
        json.dump(rows, fh)
