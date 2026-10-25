from depot import store


def run(args):
    for name in ("bins", "orders"):
        rows = [r for r in store.load(name) if r.get("qty", 1) > 0]
        store.save(name, rows)
    print("compacted")
