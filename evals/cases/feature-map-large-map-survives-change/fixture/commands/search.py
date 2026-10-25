def run(store, args):
    q = args.query.lower()
    for n in store.all():
        if q in n['title'].lower() or q in n['body'].lower():
            print(f"#{n['id']} {n['title']}")
    return 0
