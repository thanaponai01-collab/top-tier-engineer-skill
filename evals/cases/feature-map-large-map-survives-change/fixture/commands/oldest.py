def run(store, args):
    n = min(store.all(), key=lambda n: n['created'])
    print(f"{n['created']} #{n['id']} {n['title']}")
    return 0
