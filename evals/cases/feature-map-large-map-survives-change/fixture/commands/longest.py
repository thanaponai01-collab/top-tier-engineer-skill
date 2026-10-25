def run(store, args):
    n = max(store.all(), key=lambda n: len(n['body']))
    print(f"#{n['id']} {n['title']} ({len(n['body'])} chars)")
    return 0
