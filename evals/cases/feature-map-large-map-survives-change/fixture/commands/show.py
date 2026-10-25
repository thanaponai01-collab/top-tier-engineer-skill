def run(store, args):
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    print(f"#{n['id']} {n['title']}\n{n['body']}\ntags: {', '.join(n['tags'])}")
    return 0
