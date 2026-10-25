def run(store, args):
    for n in store.all():
        if not n['archived'] and (args.tag is None or args.tag in n['tags']):
            print(f"#{n['id']} {n['title']}")
    return 0
