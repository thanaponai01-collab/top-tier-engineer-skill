"""Pantry storage: one JSON file of items and a log of what was used."""
import datetime, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("PANTRY_DB", os.path.join(HERE, "pantry.json"))


def load():
    if not os.path.exists(DB):
        return {"items": [], "used": []}
    with open(DB, encoding="utf-8") as fh:
        return json.load(fh)


def save(data):
    with open(DB, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def add_item(name, qty, min_qty=1, unit="pcs"):
    data = load()
    item_id = max((i["id"] for i in data["items"]), default=0) + 1
    item = {"id": item_id, "name": name, "qty": qty, "min": min_qty, "unit": unit}
    data["items"].append(item)
    save(data)
    return item


def get(data, item_id):
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    raise KeyError(f"no item {item_id}")


def use_item(item_id, n=1):
    data = load()
    item = get(data, item_id)
    if item["qty"] < n:
        raise ValueError(f"only {item['qty']} {item['unit']} of {item['name']} left")
    item["qty"] -= n
    data["used"].append({"id": item_id, "n": n, "at": datetime.date.today().isoformat()})
    save(data)
    return item


def restock(item_id, n):
    data = load()
    item = get(data, item_id)
    item["qty"] += n
    save(data)
    return item


def shopping_list(data):
    """Items below their minimum, with how many to buy to get back to it."""
    return [dict(i, buy=i["min"] - i["qty"]) for i in data["items"] if i["qty"] < i["min"]]


def search(data, text):
    text = text.lower()
    return [i for i in data["items"] if text in i["name"].lower()]


def stats(data):
    """Uses per day since the first recorded use."""
    days = sorted(datetime.date.fromisoformat(u["at"]) for u in data["used"])
    if not days:
        return {"uses": 0, "per_day": 0.0}
    span = (days[-1] - days[0]).days + 1
    total = sum(u["qty"] for u in data["used"])
    return {"uses": total, "per_day": round(total / span, 2)}
