def run(store, args):
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    n['title'] = args.title
    store.save(notes)
    print(f'renamed #{n["id"]}')
    return 0
