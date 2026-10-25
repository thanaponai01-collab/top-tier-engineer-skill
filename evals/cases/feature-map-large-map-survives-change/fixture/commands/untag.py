def run(store, args):
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    n['tags'] = [t for t in n['tags'] if t != args.name]
    store.save(notes)
    print(f'untagged #{n["id"]} {args.name}')
    return 0
