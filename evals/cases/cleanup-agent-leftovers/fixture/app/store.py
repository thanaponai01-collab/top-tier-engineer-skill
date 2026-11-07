import json


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
    except FileNotFoundError:
        return []
    print("DEBUG loaded", len(rows), "rows from", path)
    return rows


def save(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
