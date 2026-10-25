import json, os

from app.util.dates import today

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "items.json")


def load(path=PATH):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(items, path=PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2)


def add(items, name, qty):
    item = {"id": max((i["id"] for i in items), default=0) + 1, "name": name, "qty": qty,
            "added": today()}
    items.append(item)
    return item
