import json

FILE = "balances.json"


def load():
    with open(FILE, encoding="utf-8") as fh:
        return json.load(fh)


def save(b):
    with open(FILE, "w", encoding="utf-8") as fh:
        json.dump(b, fh)
