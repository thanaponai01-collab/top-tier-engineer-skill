def run(store, args):
    for n in store.all():
        if args.tag is None or args.tag in n["tags"]:
            print(f"#{n['id']} {n['title']}  [{', '.join(n['tags'])}]")
    return 0
