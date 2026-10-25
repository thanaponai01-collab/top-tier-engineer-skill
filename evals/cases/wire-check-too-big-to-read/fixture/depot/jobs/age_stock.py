from depot import store


def run():
    rows = store.load("items")
    for r in rows:
        r["age"] += 1
    store.save("items", rows)
