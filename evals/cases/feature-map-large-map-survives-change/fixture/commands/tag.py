def run(store, args):
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    if args.name not in n['tags']:
        n['tags'].append(args.name)
    store.save(notes)
    print(f'tagged #{n["id"]} {args.name}')
    return 0
