def run(store, args):
    for n in sorted(store.all(), key=lambda n: n['created'], reverse=True)[:args.limit]:
        print(f"{n['created']} #{n['id']} {n['title']}")
    return 0
