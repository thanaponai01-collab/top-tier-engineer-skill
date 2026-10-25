def run(store, args):
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    n['pinned'] = True
    store.save(notes)
    print(f'pind #{n["id"]}')
    return 0
